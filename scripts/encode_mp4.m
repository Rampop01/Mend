#import <Foundation/Foundation.h>
#import <AVFoundation/AVFoundation.h>
#import <CoreGraphics/CoreGraphics.h>
#import <CoreText/CoreText.h>
#import <CoreVideo/CoreVideo.h>
#import <CoreMedia/CoreMedia.h>
#import <ImageIO/ImageIO.h>

static CGImageRef LoadCGImage(NSString *path) {
    NSURL *url = [NSURL fileURLWithPath:path];
    CGImageSourceRef src = CGImageSourceCreateWithURL((__bridge CFURLRef)url, NULL);
    if (!src) return NULL;
    CGImageRef img = CGImageSourceCreateImageAtIndex(src, 0, NULL);
    CFRelease(src);
    return img;
}

static void DrawTextInRect(CGContextRef ctx, NSString *text, NSString *fontName, CGFloat fontSize, CGFloat r, CGFloat g, CGFloat b, CGRect rect) {
    if (!text) return;
    CTFontRef font = CTFontCreateWithName((__bridge CFStringRef)fontName, fontSize, NULL);
    CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
    CGFloat comps[] = {r, g, b, 1.0};
    CGColorRef color = CGColorCreate(cs, comps);
    NSDictionary *attrs = @{
        (__bridge id)kCTFontAttributeName: (__bridge id)font,
        (__bridge id)kCTForegroundColorAttributeName: (__bridge id)color
    };
    NSAttributedString *attrStr = [[NSAttributedString alloc] initWithString:text attributes:attrs];
    CTFramesetterRef framesetter = CTFramesetterCreateWithAttributedString((__bridge CFAttributedStringRef)attrStr);
    CGPathRef path = CGPathCreateWithRect(rect, NULL);
    CTFrameRef frame = CTFramesetterCreateFrame(framesetter, CFRangeMake(0, attrStr.length), path, NULL);
    CTFrameDraw(frame, ctx);
    CFRelease(frame);
    CGPathRelease(path);
    CFRelease(framesetter);
    CGColorRelease(color);
    CGColorSpaceRelease(cs);
    CFRelease(font);
}

static CVPixelBufferRef CreateAnnotatedFrame(
    CGImageRef baseImg,
    NSString *badge,
    NSString *title,
    NSString *subtitle,
    double progress,
    int width,
    int height
) {
    CVPixelBufferRef pxBuffer = NULL;
    NSDictionary *attrs = @{
        (__bridge id)kCVPixelBufferCGImageCompatibilityKey: @YES,
        (__bridge id)kCVPixelBufferCGBitmapContextCompatibilityKey: @YES
    };
    CVReturn status = CVPixelBufferCreate(
        kCFAllocatorDefault,
        width,
        height,
        kCVPixelFormatType_32ARGB,
        (__bridge CFDictionaryRef)attrs,
        &pxBuffer
    );
    if (status != kCVReturnSuccess || !pxBuffer) return NULL;

    CVPixelBufferLockBaseAddress(pxBuffer, 0);
    void *baseAddr = CVPixelBufferGetBaseAddress(pxBuffer);
    CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
    CGContextRef ctx = CGBitmapContextCreate(
        baseAddr,
        width,
        height,
        8,
        CVPixelBufferGetBytesPerRow(pxBuffer),
        cs,
        kCGImageAlphaNoneSkipFirst
    );

    // Subtle zoom motion (1.0 -> 1.02)
    double scale = 1.0 + (0.02 * progress);
    CGFloat drawW = width * scale;
    CGFloat drawH = height * scale;
    CGFloat dx = (width - drawW) / 2.0;
    CGFloat dy = (height - drawH) / 2.0;

    CGContextSetRGBFillColor(ctx, 0.035, 0.05, 0.086, 1.0);
    CGContextFillRect(ctx, CGRectMake(0, 0, width, height));
    CGContextDrawImage(ctx, CGRectMake(dx, dy, drawW, drawH), baseImg);

    // Lower-third narration HUD bar
    CGRect barRect = CGRectMake(60, 26, width - 120, 114);
    CGPathRef rounded = CGPathCreateWithRoundedRect(barRect, 16, 16, NULL);
    CGContextSetRGBFillColor(ctx, 0.055, 0.082, 0.145, 0.93);
    CGContextAddPath(ctx, rounded);
    CGContextFillPath(ctx);

    CGContextSetRGBStrokeColor(ctx, 0.22, 0.74, 0.97, 0.85);
    CGContextSetLineWidth(ctx, 2.0);
    CGContextAddPath(ctx, rounded);
    CGContextStrokePath(ctx);
    CGPathRelease(rounded);

    // Progress indicator line
    CGContextSetRGBFillColor(ctx, 0.06, 0.72, 0.50, 1.0);
    CGContextFillRect(ctx, CGRectMake(64, 28, (width - 128) * progress, 4));

    // Step badge pill
    CGRect badgeRect = CGRectMake(84, 96, 265, 28);
    CGPathRef badgePath = CGPathCreateWithRoundedRect(badgeRect, 8, 8, NULL);
    CGContextSetRGBFillColor(ctx, 0.38, 0.40, 0.95, 0.96);
    CGContextAddPath(ctx, badgePath);
    CGContextFillPath(ctx);
    CGPathRelease(badgePath);

    DrawTextInRect(ctx, badge, @"HelveticaNeue-Bold", 15, 1.0, 1.0, 1.0, CGRectMake(96, 98, 245, 24));
    DrawTextInRect(ctx, title, @"HelveticaNeue-Bold", 23, 0.22, 0.74, 0.97, CGRectMake(365, 92, width - 445, 34));
    DrawTextInRect(ctx, subtitle, @"HelveticaNeue", 19, 0.95, 0.97, 1.0, CGRectMake(84, 38, width - 168, 52));

    CGContextRelease(ctx);
    CGColorSpaceRelease(cs);
    CVPixelBufferUnlockBaseAddress(pxBuffer, 0);
    return pxBuffer;
}

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        if (argc < 3) {
            fprintf(stderr, "Usage: encode_mp4 <scenes.json> <output.mp4>\n");
            return 1;
        }
        NSString *jsonPath = [NSString stringWithUTF8String:argv[1]];
        NSString *outPath = [NSString stringWithUTF8String:argv[2]];
        [[NSFileManager defaultManager] removeItemAtPath:outPath error:nil];

        NSData *jsonData = [NSData dataWithContentsOfFile:jsonPath];
        NSArray *scenes = [NSJSONSerialization JSONObjectWithData:jsonData options:0 error:nil];
        if (!scenes || scenes.count == 0) {
            fprintf(stderr, "Failed to parse scenes.json\n");
            return 1;
        }

        int width = 1920;
        int height = 1080;
        int fps = 15;

        NSString *tempVideoPath = [NSTemporaryDirectory() stringByAppendingPathComponent:@"mend_raw_video.mp4"];
        [[NSFileManager defaultManager] removeItemAtPath:tempVideoPath error:nil];

        NSError *err = nil;
        AVAssetWriter *writer = [[AVAssetWriter alloc] initWithURL:[NSURL fileURLWithPath:tempVideoPath] fileType:AVFileTypeMPEG4 error:&err];
        NSDictionary *videoSettings = @{
            AVVideoCodecKey: AVVideoCodecTypeH264,
            AVVideoWidthKey: @(width),
            AVVideoHeightKey: @(height)
        };
        AVAssetWriterInput *videoInput = [AVAssetWriterInput assetWriterInputWithMediaType:AVMediaTypeVideo outputSettings:videoSettings];
        AVAssetWriterInputPixelBufferAdaptor *adaptor = [AVAssetWriterInputPixelBufferAdaptor assetWriterInputPixelBufferAdaptorWithAssetWriterInput:videoInput sourcePixelBufferAttributes:nil];

        [writer addInput:videoInput];
        [writer startWriting];
        [writer startSessionAtSourceTime:kCMTimeZero];

        int64_t currentFrame = 0;
        NSMutableArray<NSValue *> *sceneDurations = [NSMutableArray array];

        for (NSDictionary *scene in scenes) {
            NSString *imgPath = scene[@"imagePath"];
            NSString *audioPath = scene[@"audioPath"];
            NSString *badge = scene[@"badge"] ?: @"MEND // SWITCH AI";
            NSString *title = scene[@"title"] ?: @"";
            NSString *subtitle = scene[@"subtitle"] ?: @"";

            AVURLAsset *audioAsset = [AVURLAsset URLAssetWithURL:[NSURL fileURLWithPath:audioPath] options:nil];
            double audioSec = CMTimeGetSeconds(audioAsset.duration);
            if (isnan(audioSec) || audioSec < 1.0) audioSec = 5.0;
            double durSec = audioSec + 0.65;
            int totalFrames = (int)(durSec * fps);
            if (totalFrames < 1) totalFrames = 1;

            [sceneDurations addObject:[NSValue valueWithCMTime:CMTimeMakeWithSeconds(durSec, 600)]];

            CGImageRef cgImg = LoadCGImage(imgPath);
            if (!cgImg) {
                fprintf(stderr, "Failed to load image: %s\n", [imgPath UTF8String]);
                return 1;
            }

            for (int f = 0; f < totalFrames; f++) {
                while (!videoInput.readyForMoreMediaData) {
                    [NSThread sleepForTimeInterval:0.005];
                }
                double prog = (double)f / (double)(totalFrames > 1 ? (totalFrames - 1) : 1);
                CVPixelBufferRef pb = CreateAnnotatedFrame(cgImg, badge, title, subtitle, prog, width, height);
                if (pb) {
                    CMTime pts = CMTimeMake(currentFrame, fps);
                    [adaptor appendPixelBuffer:pb withPresentationTime:pts];
                    CVPixelBufferRelease(pb);
                }
                currentFrame++;
            }
            CGImageRelease(cgImg);
        }

        [videoInput markAsFinished];
        dispatch_semaphore_t sem = dispatch_semaphore_create(0);
        [writer finishWritingWithCompletionHandler:^{
            dispatch_semaphore_signal(sem);
        }];
        dispatch_semaphore_wait(sem, DISPATCH_TIME_FOREVER);

        // Mux video and voiceover audio tracks into final MP4
        AVMutableComposition *composition = [AVMutableComposition composition];
        AVMutableCompositionTrack *compVideo = [composition addMutableTrackWithMediaType:AVMediaTypeVideo preferredTrackID:kCMPersistentTrackID_Invalid];
        AVMutableCompositionTrack *compAudio = [composition addMutableTrackWithMediaType:AVMediaTypeAudio preferredTrackID:kCMPersistentTrackID_Invalid];

        AVURLAsset *videoAsset = [AVURLAsset URLAssetWithURL:[NSURL fileURLWithPath:tempVideoPath] options:nil];
        AVAssetTrack *srcVideo = [[videoAsset tracksWithMediaType:AVMediaTypeVideo] firstObject];
        if (srcVideo) {
            [compVideo insertTimeRange:CMTimeRangeMake(kCMTimeZero, videoAsset.duration) ofTrack:srcVideo atTime:kCMTimeZero error:nil];
        }

        CMTime cursor = kCMTimeZero;
        for (NSUInteger i = 0; i < scenes.count; i++) {
            NSDictionary *scene = scenes[i];
            NSString *audioPath = scene[@"audioPath"];
            CMTime sceneDur = [sceneDurations[i] CMTimeValue];
            AVURLAsset *audioAsset = [AVURLAsset URLAssetWithURL:[NSURL fileURLWithPath:audioPath] options:nil];
            AVAssetTrack *srcAudio = [[audioAsset tracksWithMediaType:AVMediaTypeAudio] firstObject];
            if (srcAudio) {
                CMTime insertDur = CMTimeMinimum(audioAsset.duration, sceneDur);
                [compAudio insertTimeRange:CMTimeRangeMake(kCMTimeZero, insertDur) ofTrack:srcAudio atTime:cursor error:nil];
            }
            cursor = CMTimeAdd(cursor, sceneDur);
        }

        AVAssetExportSession *exporter = [[AVAssetExportSession alloc] initWithAsset:composition presetName:AVAssetExportPresetHighestQuality];
        exporter.outputURL = [NSURL fileURLWithPath:outPath];
        exporter.outputFileType = AVFileTypeMPEG4;

        dispatch_semaphore_t expSem = dispatch_semaphore_create(0);
        [exporter exportAsynchronouslyWithCompletionHandler:^{
            dispatch_semaphore_signal(expSem);
        }];
        dispatch_semaphore_wait(expSem, DISPATCH_TIME_FOREVER);

        if (exporter.status == AVAssetExportSessionStatusCompleted) {
            printf("Rendered narrated MP4 successfully: %s\n", [outPath UTF8String]);
            return 0;
        } else {
            fprintf(stderr, "Export failed: %s\n", [[exporter.error description] UTF8String]);
            return 1;
        }
    }
}

