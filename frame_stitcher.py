import cv2 as cv
import numpy as np
from collections import OrderedDict

class FrameStitcher:
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
        cv.xfeatures2d_SURF.create()  # check if the function can be called
        FEATURES_FIND_CHOICES['surf'] = cv.xfeatures2d_SURF.create
    except (AttributeError, cv.error):
        print("SURF not available")
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

    def __init__(self, initial_frames, **kwargs):
        # print("kwargs", kwargs)
        # Initialize parameters with defaults or provided kwargs
        self.matcher_type = kwargs.get('matcher', 'homography')
        self.match_conf = kwargs.get('match_conf', None)
        self.features_type = kwargs.get('features', 'sift')
        self.rangewidth = kwargs.get('rangewidth', -1)
        self.save_graph = kwargs.get('save_graph', False)
        self.expos_comp = kwargs.get('expos_comp', 'channel_blocks')
        self.expos_comp_nr_feeds = kwargs.get('expos_comp_nr_feeds', 1)
        self.expos_comp_block_size = kwargs.get('expos_comp_block_size', 32)
        self.compose_megapix = kwargs.get('compose_megapix', -1)
        self.conf_thresh = kwargs.get('conf_thresh', 0.3)
        self.ba_refine_mask = kwargs.get('ba_refine_mask', 'xxxxx')
        self.wave_correct = kwargs.get('wave_correct', cv.detail.WAVE_CORRECT_HORIZ)
        self.warp_type = kwargs.get('warp_type', 'cylindrical')
        self.blend_type = kwargs.get('blend_type', 'feather')
        self.blend_strength = kwargs.get('blend_strength', 50)
        self.timelapse = kwargs.get('timelapse', False)
        self.work_megapix = kwargs.get('work_megapix', 0.6)
        self.seam_megapix = kwargs.get('seam_megapix', 0.1)
        self.is_compose_scale_set = False
        self.is_work_scale_set = False
        self.is_seam_scale_set = False
        self.compose_scale = 1

        # Extract features from initial frames
        self.features, self.images, self.full_img_sizes, self.seam_work_aspect, self.work_scale, self.p = self.feature_extractor(initial_frames)

        # Leave only the largest component
        self.indices = cv.detail.leaveBiggestComponent(self.features, self.p, self.conf_thresh)
        self.num_images = len(self.full_img_sizes)
        if self.num_images < 2:
            print("Need more images")
            exit()

        # Estimate camera parameters
        estimator = cv.detail_HomographyBasedEstimator()
        b, self.cameras = estimator.apply(self.features, self.p, None)
        if not b:
            print("Homography estimation failed.")
            exit()
        for cam in self.cameras:
            cam.R = cam.R.astype(np.float32)

        # Bundle adjustment
        adjuster = cv.detail_BundleAdjusterRay()
        adjuster.setConfThresh(self.conf_thresh)
        refine_mask = np.zeros((3, 3), np.uint8)
        if self.ba_refine_mask[0] == 'x':
            refine_mask[0, 0] = 1
        if self.ba_refine_mask[1] == 'x':
            refine_mask[0, 1] = 1
        if self.ba_refine_mask[2] == 'x':
            refine_mask[0, 2] = 1
        if self.ba_refine_mask[3] == 'x':
            refine_mask[1, 1] = 1
        if self.ba_refine_mask[4] == 'x':
            refine_mask[1, 2] = 1
        adjuster.setRefinementMask(refine_mask)
        b, self.cameras = adjuster.apply(self.features, self.p, self.cameras)
        if not b:
            print("Camera parameters adjusting failed.")
            exit()
        for cam in self.cameras:
            cam.R = cam.R.astype(np.float32)

        # Wave correction
        if self.wave_correct is not None:
            rmats = []
            for cam in self.cameras:
                rmats.append(np.copy(cam.R))
            rmats = cv.detail.waveCorrect(rmats, self.wave_correct)
            for idx, cam in enumerate(self.cameras):
                cam.R = rmats[idx]

        # Warp images and prepare for blending
        self.prepare_warping_and_blending()

    def get_matcher(self):
        try_cuda = True
        matcher_type = self.matcher_type
        if self.match_conf is None:
            if self.features_type == 'orb':
                match_conf = 0.3
            else:
                match_conf = 0.65
        else:
            match_conf = self.match_conf
        range_width = self.rangewidth
        if matcher_type == "affine":
            matcher = cv.detail_AffineBestOf2NearestMatcher(False, try_cuda, match_conf)
        elif range_width == -1:
            matcher = cv.detail_BestOf2NearestMatcher(try_cuda, match_conf)
        else:
            matcher = cv.detail_BestOf2NearestRangeMatcher(range_width, try_cuda, match_conf)
        return matcher

    def get_compensator(self):
        expos_comp_type = self.EXPOS_COMP_CHOICES[self.expos_comp]
        if expos_comp_type == cv.detail.ExposureCompensator_CHANNELS:
            compensator = cv.detail_ChannelsCompensator(self.expos_comp_nr_feeds)
        elif expos_comp_type == cv.detail.ExposureCompensator_CHANNELS_BLOCKS:
            compensator = cv.detail_BlocksChannelsCompensator(
                self.expos_comp_block_size, self.expos_comp_block_size,
                self.expos_comp_nr_feeds
            )
        else:
            compensator = cv.detail.ExposureCompensator_createDefault(expos_comp_type)
        return compensator

    def feature_extractor(self, cv_images):
        finder = self.FEATURES_FIND_CHOICES[self.features_type]()
        seam_work_aspect = 1
        full_img_sizes = []
        features = []
        images = []
        for image in cv_images:
            full_img = image
            if full_img is None:
                print("Cannot read images")
                exit()
            full_img_sizes.append((full_img.shape[1], full_img.shape[0]))
            if self.work_megapix < 0:
                img = full_img
                work_scale = 1
                self.is_work_scale_set = True
            else:
                if self.is_work_scale_set is False:
                    work_scale = min(1.0, np.sqrt(self.work_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
                    self.is_work_scale_set = True
                img = cv.resize(src=full_img, dsize=None, fx=work_scale, fy=work_scale, interpolation=cv.INTER_LINEAR_EXACT)
            if self.is_seam_scale_set is False:
                if self.seam_megapix > 0:
                    seam_scale = min(1.0, np.sqrt(self.seam_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
                else:
                    seam_scale = 1.0
                seam_work_aspect = seam_scale / work_scale
                self.is_seam_scale_set = True
            img_feat = cv.detail.computeImageFeatures2(finder, img)
            features.append(img_feat)
            img = cv.resize(src=full_img, dsize=None, fx=seam_scale, fy=seam_scale, interpolation=cv.INTER_LINEAR_EXACT)
            images.append(img)
        matcher = self.get_matcher()
        p = matcher.apply2(features)
        matcher.collectGarbage()
        return features, images, full_img_sizes, seam_work_aspect, work_scale, p

    def prepare_warping_and_blending(self):
        # Prepare masks
        self.masks = []
        for i in range(0, self.num_images):
            um = cv.UMat(255 * np.ones((self.images[i].shape[0], self.images[i].shape[1]), np.uint8))
            self.masks.append(um)

        # Warp images and masks
        self.corners = []
        self.masks_warped = []
        self.images_warped = []
        self.sizes = []
        focals = [cam.focal for cam in self.cameras]
        focals.sort()
        if len(focals) % 2 == 1:
            self.warped_image_scale = focals[len(focals) // 2]
        else:
            self.warped_image_scale = (focals[len(focals) // 2] + focals[len(focals) // 2 - 1]) / 2
        self.warper = cv.PyRotationWarper(self.warp_type, self.warped_image_scale * self.seam_work_aspect)
        for idx in range(0, self.num_images):
            K = self.cameras[idx].K().astype(np.float32)
            swa = self.seam_work_aspect
            K[0, 0] *= swa
            K[0, 2] *= swa
            K[1, 1] *= swa
            K[1, 2] *= swa
            corner, image_wp = self.warper.warp(self.images[idx], K, self.cameras[idx].R, cv.INTER_LINEAR, cv.BORDER_REFLECT)
            self.corners.append(corner)
            self.sizes.append((image_wp.shape[1], image_wp.shape[0]))
            self.images_warped.append(image_wp)
            p, mask_wp = self.warper.warp(self.masks[idx], K, self.cameras[idx].R, cv.INTER_NEAREST, cv.BORDER_CONSTANT)
            self.masks_warped.append(mask_wp.get())

        # Convert images to float32
        self.images_warped_f = []
        for img in self.images_warped:
            imgf = img.astype(np.float32)
            self.images_warped_f.append(imgf)

        # Compensate exposure
        self.compensator = self.get_compensator()
        self.compensator.feed(corners=self.corners, images=self.images_warped, masks=self.masks_warped)

    def stitch_frames(self, frames):
        is_compose_scale_set = False
        compose_scale = 1
        corners = []
        sizes = []
        blender = None

        for idx, frame in enumerate(frames):
            full_img = frame
            if not is_compose_scale_set:
                if self.compose_megapix > 0:
                    compose_scale = min(1.0, np.sqrt(self.compose_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
                is_compose_scale_set = True
                compose_work_aspect = compose_scale / self.work_scale
                self.warped_image_scale *= compose_work_aspect
                warper = cv.PyRotationWarper(self.warp_type, self.warped_image_scale)
                for i in range(len(frames)):
                    self.cameras[i].focal *= compose_work_aspect
                    self.cameras[i].ppx *= compose_work_aspect
                    self.cameras[i].ppy *= compose_work_aspect
                    sz = (int(round(self.full_img_sizes[i][0] * compose_scale)),
                          int(round(self.full_img_sizes[i][1] * compose_scale)))
                    K = self.cameras[i].K().astype(np.float32)
                    roi = warper.warpRoi(sz, K, self.cameras[i].R)
                    corners.append(roi[0:2])
                    sizes.append(roi[2:4])

            if abs(compose_scale - 1) > 1e-1:
                img = cv.resize(src=full_img, dsize=None, fx=compose_scale, fy=compose_scale,
                                interpolation=cv.INTER_LINEAR_EXACT)
            else:
                img = full_img
            _img_size = (img.shape[1], img.shape[0])
            K = self.cameras[idx].K().astype(np.float32)
            corner, image_warped = warper.warp(img, K, self.cameras[idx].R, cv.INTER_LINEAR, cv.BORDER_REFLECT)
            mask = 255 * np.ones((img.shape[0], img.shape[1]), np.uint8)
            p, mask_warped = warper.warp(mask, K, self.cameras[idx].R, cv.INTER_NEAREST, cv.BORDER_CONSTANT)
            self.compensator.apply(idx, corners[idx], image_warped, mask_warped)
            image_warped_s = image_warped.astype(np.int16)
            dilated_mask = cv.dilate(mask_warped, None)
            seam_mask = cv.resize(dilated_mask, (mask_warped.shape[1], mask_warped.shape[0]), 0, 0, cv.INTER_LINEAR_EXACT)
            mask_warped = cv.bitwise_and(seam_mask, mask_warped)

            if blender is None and not self.timelapse:
                blender = cv.detail.Blender_createDefault(cv.detail.Blender_NO)
                dst_sz = cv.detail.resultRoi(corners=corners, sizes=sizes)
                blend_width = np.sqrt(dst_sz[2] * dst_sz[3]) * self.blend_strength / 100
                if blend_width < 1:
                    blender = cv.detail.Blender_createDefault(cv.detail.Blender_NO)
                elif self.blend_type == "multiband":
                    blender = cv.detail_MultiBandBlender()
                    blender.setNumBands((np.log(blend_width) / np.log(2.) - 1.).astype(np.int32))
                elif self.blend_type == "feather":
                    blender = cv.detail_FeatherBlender()
                    blender.setSharpness(1. / blend_width)
                blender.prepare(dst_sz)

            blender.feed(cv.UMat(image_warped_s), mask_warped, corners[idx])

        if not self.timelapse:
            result = None
            result_mask = None
            result, result_mask = blender.blend(result, result_mask)
            # zoom_x = 600.0 / result.shape[1]
            dst = cv.normalize(src=result, dst=None, alpha=255., norm_type=cv.NORM_MINMAX, dtype=cv.CV_8U)
            # dst = cv.resize(dst, dsize=None, fx=zoom_x, fy=zoom_x)
            return dst
