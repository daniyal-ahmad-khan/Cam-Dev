"""
Stitching sample (advanced)
===========================

Show how to use Stitcher API from python.
"""

# Python 2/3 compatibility
from __future__ import print_function

import argparse
from collections import OrderedDict

import cv2 as cv
import numpy as np
import time
EXPOS_COMP_CHOICES = OrderedDict()
EXPOS_COMP_CHOICES['gain_blocks'] = cv.detail.ExposureCompensator_GAIN_BLOCKS
EXPOS_COMP_CHOICES['gain'] = cv.detail.ExposureCompensator_GAIN
EXPOS_COMP_CHOICES['channel'] = cv.detail.ExposureCompensator_CHANNELS
EXPOS_COMP_CHOICES['channel_blocks'] = cv.detail.ExposureCompensator_CHANNELS_BLOCKS
EXPOS_COMP_CHOICES['no'] = cv.detail.ExposureCompensator_NO

BA_COST_CHOICES = OrderedDict()
BA_COST_CHOICES['ray'] = cv.detail_BundleAdjusterRay
BA_COST_CHOICES['reproj'] = cv.detail_BundleAdjusterReproj
BA_COST_CHOICES['affine'] = cv.detail_BundleAdjusterAffinePartial
BA_COST_CHOICES['no'] = cv.detail_NoBundleAdjuster

FEATURES_FIND_CHOICES = OrderedDict()
try:
    cv.xfeatures2d_SURF.create() # check if the function can be called
    FEATURES_FIND_CHOICES['surf'] = cv.xfeatures2d_SURF.create
except (AttributeError, cv.error) as e:
    print("SURF not available")
# if SURF not available, ORB is default
FEATURES_FIND_CHOICES['orb'] = cv.ORB.create
try:
    FEATURES_FIND_CHOICES['sift'] = cv.SIFT_create
except AttributeError:
    print("SIFT not available")
try:
    FEATURES_FIND_CHOICES['brisk'] = cv.BRISK_create
except AttributeError:
    print("BRISK not available")
try:
    FEATURES_FIND_CHOICES['akaze'] = cv.AKAZE_create
except AttributeError:
    print("AKAZE not available")

SEAM_FIND_CHOICES = OrderedDict()
SEAM_FIND_CHOICES['gc_color'] = cv.detail_GraphCutSeamFinder('COST_COLOR')
SEAM_FIND_CHOICES['gc_colorgrad'] = cv.detail_GraphCutSeamFinder('COST_COLOR_GRAD')
SEAM_FIND_CHOICES['dp_color'] = cv.detail_DpSeamFinder('COLOR')
SEAM_FIND_CHOICES['dp_colorgrad'] = cv.detail_DpSeamFinder('COLOR_GRAD')
SEAM_FIND_CHOICES['voronoi'] = cv.detail.SeamFinder_createDefault(cv.detail.SeamFinder_VORONOI_SEAM)
SEAM_FIND_CHOICES['no'] = cv.detail.SeamFinder_createDefault(cv.detail.SeamFinder_NO)

ESTIMATOR_CHOICES = OrderedDict()
ESTIMATOR_CHOICES['homography'] = cv.detail_HomographyBasedEstimator
ESTIMATOR_CHOICES['affine'] = cv.detail_AffineBasedEstimator

WARP_CHOICES = (
    'spherical',
    'plane',
    'affine',
    'cylindrical',
    'fisheye',
    'stereographic',
    'compressedPlaneA2B1',
    'compressedPlaneA1.5B1',
    'compressedPlanePortraitA2B1',
    'compressedPlanePortraitA1.5B1',
    'paniniA2B1',
    'paniniA1.5B1',
    'paniniPortraitA2B1',
    'paniniPortraitA1.5B1',
    'mercator',
    'transverseMercator',
)

WAVE_CORRECT_CHOICES = OrderedDict()
WAVE_CORRECT_CHOICES['horiz'] = cv.detail.WAVE_CORRECT_HORIZ
WAVE_CORRECT_CHOICES['no'] = None
WAVE_CORRECT_CHOICES['vert'] = cv.detail.WAVE_CORRECT_VERT


def get_matcher(args):
    try_cuda = True
    matcher_type = args.matcher
    if args.match_conf is None:
        if args.features == 'orb':
            match_conf = 0.3
        else:
            match_conf = 0.65
    else:
        match_conf = args.match_conf
    range_width = args.rangewidth
    if matcher_type == "affine":
        matcher = cv.detail_AffineBestOf2NearestMatcher(False, try_cuda, match_conf)
    elif range_width == -1:
        matcher = cv.detail_BestOf2NearestMatcher(try_cuda, match_conf)
    else:
        matcher = cv.detail_BestOf2NearestRangeMatcher(range_width, try_cuda, match_conf)
    return matcher


def get_compensator(args):
    expos_comp_type = EXPOS_COMP_CHOICES[args.expos_comp]
    expos_comp_nr_feeds = args.expos_comp_nr_feeds
    expos_comp_block_size = args.expos_comp_block_size
    # expos_comp_nr_filtering = args.expos_comp_nr_filtering
    if expos_comp_type == cv.detail.ExposureCompensator_CHANNELS:
        compensator = cv.detail_ChannelsCompensator(expos_comp_nr_feeds)
        # compensator.setNrGainsFilteringIterations(expos_comp_nr_filtering)
    elif expos_comp_type == cv.detail.ExposureCompensator_CHANNELS_BLOCKS:
        compensator = cv.detail_BlocksChannelsCompensator(
            expos_comp_block_size, expos_comp_block_size,
            expos_comp_nr_feeds
        )
        # compensator.setNrGainsFilteringIterations(expos_comp_nr_filtering)
    else:
        compensator = cv.detail.ExposureCompensator_createDefault(expos_comp_type)
    return compensator

def feature_extractor(args,cv_images):
    work_megapix = 0.6
    seam_megapix = 0.1
    finder = FEATURES_FIND_CHOICES["sift"]()
    seam_work_aspect = 1
    full_img_sizes = []
    features = []
    images = []
    is_work_scale_set = False
    is_seam_scale_set = False
    
    for image in cv_images:
        full_img = image
        if full_img is None:
            print("Cannot read images")
            exit()
        full_img_sizes.append((full_img.shape[1], full_img.shape[0]))
        if work_megapix < 0:
            img = full_img
            work_scale = 1
            is_work_scale_set = True
        else:
            if is_work_scale_set is False:
                work_scale = min(1.0, np.sqrt(work_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
                is_work_scale_set = True
            img = cv.resize(src=full_img, dsize=None, fx=work_scale, fy=work_scale, interpolation=cv.INTER_LINEAR_EXACT)
        if is_seam_scale_set is False:
            if seam_megapix > 0:
                seam_scale = min(1.0, np.sqrt(seam_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
            else:
                seam_scale = 1.0
            seam_work_aspect = seam_scale / work_scale
            is_seam_scale_set = True
        img_feat = cv.detail.computeImageFeatures2(finder, img)
        features.append(img_feat)
        img = cv.resize(src=full_img, dsize=None, fx=seam_scale, fy=seam_scale, interpolation=cv.INTER_LINEAR_EXACT)
        images.append(img)
    matcher = get_matcher(args)
    p = matcher.apply2(features)
    matcher.collectGarbage()
    return features,images,full_img_sizes,seam_work_aspect, work_scale,p
        


def stitch_frame(args, cv_images,full_img_sizes,work_scale,cameras,warped_image_scale,images_warped_f,compensator,corners,masks_warped):
    args.is_compose_scale_set = False
    # seam_finder = cv.detail_DpSeamFinder('COLOR')
    seam_finder = cv.detail.SeamFinder_createDefault(cv.detail.SeamFinder_NO)
    masks_warped = seam_finder.find(images_warped_f, corners, masks_warped)
    compose_scale = 1
    corners = []
    sizes = []
    blender = None
    timelapser = None
    # https://github.com/opencv/opencv/blob/4.x/samples/cpp/stitching_detailed.cpp#L725 ?
    start_time = time.time()
    for idx, igm in enumerate(cv_images):
        full_img = igm
        if not args.is_compose_scale_set:
            if args.compose_megapix > 0:
                compose_scale = min(1.0, np.sqrt(args.compose_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
            args.is_compose_scale_set = True
            compose_work_aspect = compose_scale / work_scale
            warped_image_scale *= compose_work_aspect
            
            warper = cv.PyRotationWarper(args.warp_type, warped_image_scale)
            
            
            for i in range(0, len(cv_images)):
                cameras[i].focal *= compose_work_aspect
                cameras[i].ppx *= compose_work_aspect
                cameras[i].ppy *= compose_work_aspect
                sz = (int(round(full_img_sizes[i][0] * compose_scale)),
                      int(round(full_img_sizes[i][1] * compose_scale)))
                K = cameras[i].K().astype(np.float32)
                roi = warper.warpRoi(sz, K, cameras[i].R)
                corners.append(roi[0:2])
                sizes.append(roi[2:4])
            
        
        if abs(compose_scale - 1) > 1e-1:
            img = cv.resize(src=full_img, dsize=None, fx=compose_scale, fy=compose_scale,
                            interpolation=cv.INTER_LINEAR_EXACT)
        else:
            img = full_img
        _img_size = (img.shape[1], img.shape[0])
        K = cameras[idx].K().astype(np.float32)
        corner, image_warped = warper.warp(img, K, cameras[idx].R, cv.INTER_LINEAR, cv.BORDER_REFLECT)
        mask = 255 * np.ones((img.shape[0], img.shape[1]), np.uint8)
        p, mask_warped = warper.warp(mask, K, cameras[idx].R, cv.INTER_NEAREST, cv.BORDER_CONSTANT)
        compensator.apply(idx, corners[idx], image_warped, mask_warped)
        image_warped_s = image_warped.astype(np.int16)
        dilated_mask = cv.dilate(masks_warped[idx], None)
        seam_mask = cv.resize(dilated_mask, (mask_warped.shape[1], mask_warped.shape[0]), 0, 0, cv.INTER_LINEAR_EXACT)
        mask_warped = cv.bitwise_and(seam_mask, mask_warped)
        # start_time = time.time()
        if blender is None and not args.timelapse:
            blender = cv.detail.Blender_createDefault(cv.detail.Blender_NO)
            dst_sz = cv.detail.resultRoi(corners=corners, sizes=sizes)
            blend_width = np.sqrt(dst_sz[2] * dst_sz[3]) * args.blend_strength / 100
            if blend_width < 1:
                blender = cv.detail.Blender_createDefault(cv.detail.Blender_NO)
            elif args.blend_type == "multiband":
                blender = cv.detail_MultiBandBlender()
                blender.setNumBands((np.log(blend_width) / np.log(2.) - 1.).astype(np.int32))
            elif args.blend_type == "feather":
                blender = cv.detail_FeatherBlender()
                blender.setSharpness(1. / blend_width)
            blender.prepare(dst_sz)
        # elif timelapser is None and timelapse:
        #     timelapser = cv.detail.Timelapser_createDefault(timelapse_type)
        #     timelapser.initialize(corners, sizes)
        if args.timelapse:
            exit()
        else:
            blender.feed(cv.UMat(image_warped_s), mask_warped, corners[idx])
    # time_elapsed = time.time() - start_time
    # print("Time elapsed 2: %.2f sec" % time_elapsed)
    if not args.timelapse:
        result = None
        result_mask = None
        result, result_mask = blender.blend(result, result_mask)
        # cv.imwrite(result_name, result)
        zoom_x = 600.0 / result.shape[1]
        dst = cv.normalize(src=result, dst=None, alpha=255., norm_type=cv.NORM_MINMAX, dtype=cv.CV_8U)
        dst = cv.resize(dst, dsize=None, fx=zoom_x, fy=zoom_x)
        return dst

    

def main():
    args = OrderedDict()
    args.matcher = "homography"
    args.match_conf = None
    args.features = "sift"
    args.rangewidth = -1
    args.save_graph = None
    args.expos_comp = "channel_blocks"
    args.expos_comp_nr_feeds = 1
    args.expos_comp_block_size = 32

    args.compose_megapix = -1
    args.conf_thresh = 0.3
    args.ba_refine_mask = "xxxxx"
    # wave_correct = cv.detail.WAVE_CORRECT_HORIZ
    args.wave_correct = cv.detail.WAVE_CORRECT_HORIZ
    
    if args.save_graph is None:
        args.save_graph = False
    else:
        args.save_graph = True

    args.warp_type = "cylindrical"
    args.blend_type = "feather"
    args.blend_strength = 50
    args.timelapse = False
    

    
    # Open the video files
    cap = cv.VideoCapture("output2x.mp4")
    cap1 = cv.VideoCapture("output1x.mp4")
    cap2 = cv.VideoCapture("output0x.mp4")
    
    # Read the first frames to get the size for VideoWriter
    ret, frame0 = cap.read()
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    if not ret or not ret1 or not ret2:
        print("Error: Could not read frames from one or more video files.")
        return

    # Call the feature extractor (Assumed to be defined elsewhere)
    features, images, full_img_sizes, seam_work_aspect, work_scale, p = feature_extractor(args, [frame0, frame1, frame2])
    args.indices = cv.detail.leaveBiggestComponent(features, p, args.conf_thresh)
    num_images = len(full_img_sizes)

    # Estimate camera parameters
    estimator = cv.detail_HomographyBasedEstimator()
    b, cameras = estimator.apply(features, p, None)
    if not b:
        print("Homography estimation failed.")
        exit()
    for cam in cameras:
        cam.R = cam.R.astype(np.float32)

    adjuster = cv.detail_BundleAdjusterRay()
    adjuster.setConfThresh(args.conf_thresh)
    refine_mask = np.zeros((3, 3), np.uint8)
    if args.ba_refine_mask[0] == 'x':
        refine_mask[0, 0] = 1
    if args.ba_refine_mask[1] == 'x':
        refine_mask[0, 1] = 1
    if args.ba_refine_mask[2] == 'x':
        refine_mask[0, 2] = 1
    if args.ba_refine_mask[3] == 'x':
        refine_mask[1, 1] = 1
    if args.ba_refine_mask[4] == 'x':
        refine_mask[1, 2] = 1
    adjuster.setRefinementMask(refine_mask)
    b, cameras = adjuster.apply(features, p, cameras)
    if not b:
        print("Camera parameters adjusting failed.")
        exit()
    focals = []
    for cam in cameras:
        focals.append(cam.focal)
    focals.sort()
    if len(focals) % 2 == 1:
        warped_image_scale = focals[len(focals) // 2]
    else:
        warped_image_scale = (focals[len(focals) // 2] + focals[len(focals) // 2 - 1]) / 2
    if args.wave_correct is not None:
        rmats = []
        for cam in cameras:
            rmats.append(np.copy(cam.R))
        rmats = cv.detail.waveCorrect(rmats, args.wave_correct)
        for idx, cam in enumerate(cameras):
            cam.R = rmats[idx]



    masks = []
    for i in range(0, num_images):
        um = cv.UMat(255 * np.ones((images[i].shape[0], images[i].shape[1]), np.uint8))
        masks.append(um)
    # Get frame size from the result

    


    img_subset = []
    img_names_subset = []
    full_img_sizes_subset = []
    for i in range(len(args.indices)):
        img_subset.append(images[args.indices[i]])
        full_img_sizes_subset.append(full_img_sizes[args.indices[i]])
    images = img_subset
    full_img_sizes = full_img_sizes_subset
    num_images = len(full_img_sizes)
    # print(num_images)
    if num_images < 2:
        print("Need more images")
        exit()

    
    corners = []
    masks_warped = []
    images_warped = []
    sizes = []
    
    # start_time = time.time()
    warper = cv.PyRotationWarper(args.warp_type, warped_image_scale * seam_work_aspect)  # warper could be nullptr?
    for idx in range(0, num_images):
        K = cameras[idx].K().astype(np.float32)
        swa = seam_work_aspect
        K[0, 0] *= swa
        K[0, 2] *= swa
        K[1, 1] *= swa
        K[1, 2] *= swa
        corner, image_wp = warper.warp(images[idx], K, cameras[idx].R, cv.INTER_LINEAR, cv.BORDER_REFLECT)
        corners.append(corner)
        sizes.append((image_wp.shape[1], image_wp.shape[0]))
        images_warped.append(image_wp)
        p, mask_wp = warper.warp(masks[idx], K, cameras[idx].R, cv.INTER_NEAREST, cv.BORDER_CONSTANT)
        masks_warped.append(mask_wp.get())

    images_warped_f = []
    for img in images_warped:
        imgf = img.astype(np.float32)
        images_warped_f.append(imgf)
    # start_time = time.time()
    compensator = get_compensator(args)
    compensator.feed(corners=corners, images=images_warped, masks=masks_warped)
    # time_elapsed = time.time() - start_time
    # print("Time elapsed 1: %.2f sec" % time_elapsed)






    result = stitch_frame(args, [frame0, frame1, frame2], full_img_sizes,work_scale,cameras,warped_image_scale,images_warped_f,compensator,corners,masks_warped)
    frame_height, frame_width = result.shape[:2]

    # Set up VideoWriter object for writing to MP4
    fps = 25
    fourcc = cv.VideoWriter_fourcc(*'mp4v')  # Codec for mp4
    out = cv.VideoWriter('stitched_output_abhiy.mp4', fourcc, fps, (frame_width, frame_height))

    # Main loop to process frames and write to video
    while True:
        start_time = time.time()
        # features, images, full_img_sizes, seam_work_aspect, work_scale, p = feature_extractor(args, [frame0, frame1, frame2])
        ret, frame0 = cap.read()
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        
        # Break loop if any video ends
        if not ret or not ret1 or not ret2:
            break
        if len(focals) % 2 == 1:
            warped_image_scale = focals[len(focals) // 2]
        else:
            warped_image_scale = (focals[len(focals) // 2] + focals[len(focals) // 2 - 1]) / 2
        # Call the frame stitching function (Assumed to be defined elsewhere)
        result = stitch_frame(args, [frame0, frame1, frame2], full_img_sizes,work_scale,cameras,warped_image_scale,images_warped_f,compensator,corners,masks_warped)
        
        # Show the result frame (optional)
        cv.imshow("result", result)

        # Write the result frame to the output video
        out.write(result)
        time_elapsed = time.time() - start_time
        print("Time elapsed: %.2f sec" % time_elapsed)
        # Break loop if 'q' is pressed
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    # Release all resources
    cap.release()
    cap1.release()
    cap2.release()
    out.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()
    cv.destroyAllWindows()