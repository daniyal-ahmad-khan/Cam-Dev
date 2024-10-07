from PyQt5.QtWidgets import QWidget, QFormLayout, QSpinBox, QCheckBox, QDoubleSpinBox, QComboBox, QLabel

class StitchingSettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # CUDA usage
        self.try_cuda = QCheckBox("Try to use CUDA")
        self.try_cuda.setChecked(True)

        # Resolution for image registration step
        self.work_megapix = QDoubleSpinBox()
        self.work_megapix.setRange(-1.0, 10.0)
        self.work_megapix.setSingleStep(0.1)
        self.work_megapix.setValue(-1.0)

        # Features type
        self.features = QComboBox()
        self.features.addItems(['sift', 'orb', 'surf', 'brisk', 'akaze'])

        # Matcher type
        self.matcher = QComboBox()
        self.matcher.addItems(['homography', 'affine'])

        # Estimator type
        self.estimator = QComboBox()
        self.estimator.addItems(['homography', 'affine'])
        self.conf_thresh = QDoubleSpinBox()
        self.conf_thresh.setRange(0.0, 1.0)
        self.conf_thresh.setSingleStep(0.05)
        self.conf_thresh.setValue(0.3)

        # Bundle adjuster type
        self.ba = QComboBox()
        self.ba.addItems(['ray', 'reproj', 'affine', 'no'])

        # BA refinement mask
        self.ba_refine_mask = QLabel("Refinement mask: xxxxx")

        # Wave correction
        # self.wave_correct = QComboBox()
        # self.wave_correct.addItems(['horiz', 'vert', 'no'])

        # Save graph
        self.save_graph = QCheckBox("Save matches graph")
        self.save_graph.setChecked(False)

        # Warp type
        self.warp = QComboBox()
        self.warp.addItems([
            'cylindrical', 'plane', 'affine', 'spherical', 'fisheye', 'stereographic',
            'compressedPlaneA2B1', 'compressedPlaneA1.5B1', 'compressedPlanePortraitA2B1',
            'compressedPlanePortraitA1.5B1', 'paniniA2B1', 'paniniA1.5B1',
            'paniniPortraitA2B1', 'paniniPortraitA1.5B1', 'mercator', 'transverseMercator'
        ])

        # Seam finding method
        self.seam = QComboBox()
        self.seam.addItems(['gc_color', 'gc_colorgrad', 'dp_color', 'dp_colorgrad', 'voronoi', 'no'])

        # Compositing resolution
        self.compose_megapix = QDoubleSpinBox()
        self.compose_megapix.setRange(-1.0, 10.0)
        self.compose_megapix.setSingleStep(0.1)
        self.compose_megapix.setValue(-1)

        # Exposure compensation method
        self.expos_comp = QComboBox()
        self.expos_comp.addItems(['channel_blocks', 'gain', 'channel', 'gain_blocks', 'no'])

        # Blending method
        self.blend = QComboBox()
        self.blend.addItems(['multiband', 'feather', 'no'])

        # Blending strength
        self.blend_strength = QSpinBox()
        self.blend_strength.setRange(0, 100)
        self.blend_strength.setSingleStep(1)
        self.blend_strength.setValue(5)

        # Output
        self.output = QLabel("Output: result.jpg")

        # Timelapse option
        self.timelapse = QCheckBox("Output timelapse frames")

        # Range width
        self.rangewidth = QSpinBox()
        self.rangewidth.setRange(-1, 100)
        self.rangewidth.setValue(-1)

        # Add all widgets to layout
        layout.addRow("Try CUDA:", self.try_cuda)
        layout.addRow("Work Megapixels:", self.work_megapix)
        layout.addRow("Features:", self.features)
        layout.addRow("Matcher:", self.matcher)
        layout.addRow("Estimator:", self.estimator)
        # layout.addRow("Match Confidence:", self.match_conf)
        layout.addRow("Confidence Threshold:", self.conf_thresh)
        layout.addRow("Bundle Adjuster:", self.ba)
        layout.addRow("Refinement Mask:", self.ba_refine_mask)
        # layout.addRow("Wave Correction:", self.wave_correct)
        layout.addRow("Save Graph:", self.save_graph)
        layout.addRow("Warp Type:", self.warp)
        layout.addRow("Seam Finding Method:", self.seam)
        layout.addRow("Compose Megapixels:", self.compose_megapix)
        layout.addRow("Exposure Compensation Method:", self.expos_comp)
        layout.addRow("Blending Method:", self.blend)
        layout.addRow("Blending Strength:", self.blend_strength)
        layout.addRow("Output:", self.output)
        layout.addRow("Timelapse:", self.timelapse)
        layout.addRow("Range Width:", self.rangewidth)

        self.setLayout(layout)

    def get_settings(self):
        settings = {
            'try_cuda': self.try_cuda.isChecked(),
            'work_megapix': self.work_megapix.value(),
            'features': self.features.currentText(),
            'matcher': self.matcher.currentText(),
            'estimator': self.estimator.currentText(),
            # 'match_conf': self.match_conf.value(),
            'conf_thresh': self.conf_thresh.value(),
            'ba': self.ba.currentText(),
            'ba_refine_mask': self.ba_refine_mask.text().replace('Refinement mask: ', ''),
            # 'wave_correct': self.wave_correct.currentText(),
            'save_graph': self.save_graph.isChecked(),
            'warp_type': self.warp.currentText(),
            'seam': self.seam.currentText(),
            'compose_megapix': self.compose_megapix.value(),
            'expos_comp': self.expos_comp.currentText(),
            'blend_type': self.blend.currentText(),
            'blend_strength': self.blend_strength.value(),
            'output': self.output.text().replace('Output: ', ''),
            'timelapse': self.timelapse.isChecked(),
            'rangewidth': self.rangewidth.value()
        }
        return settings

