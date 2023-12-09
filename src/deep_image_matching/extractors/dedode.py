import kornia as K
import kornia.feature as KF
import numpy as np
import torch

from .extractor_base import ExtractorBase, FeaturesDict


import torch
import sys

from ..thirdparty.DeDoDe.DeDoDe import dedode_detector_L, dedode_descriptor_G
from ..thirdparty.DeDoDe.DeDoDe.utils import *
from PIL import Image
import cv2
import numpy as np

class DeDoDe(ExtractorBase):
    default_conf = {
        "name:": "",
    }
    required_inputs = ["image"]
    grayscale = False
    descriptor_size = 256
    detection_noise = 2.0

    def __init__(self, config: dict):
        # Init the base class
        super().__init__(config)

        cfg = self._config.get("extractor")

        # Load extractor
        self._extractor = KF.KeyNetAffNetHardNet(
            num_features=cfg["n_features"],
            upright=cfg["upright"],
            device=self._device,
        )

        import torchvision.transforms as transforms
        self.normalizer = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    @torch.no_grad()
    def _extract(self, image: np.ndarray) -> np.ndarray:
        #image = K.image_to_tensor(image, False).float() / 255.0
        #if self._device == "cpu":
        #    image = image.cpu()
        #if self._device == "cuda":
        #    image = image.cuda()
        #keypts = self._extractor(image)
        #laf = keypts[0].cpu().detach().numpy()
        #kpts = keypts[0].cpu().detach().numpy()[-1, :, :, -1]
        #des = keypts[2].cpu().detach().numpy()[-1, :, :].T
        #feats = FeaturesDict(keypoints=kpts, descriptors=des)

        H, W, C = image.shape

        detector = dedode_detector_L(weights = torch.load("./src/deep_image_matching/thirdparty/weights/dedode/dedode_detector_L.pth", map_location = self._device))
        descriptor = dedode_descriptor_G(weights = torch.load("./src/deep_image_matching/thirdparty/weights/dedode/dedode_descriptor_G.pth", map_location = self._device))
        #im_A = Image.open(im_A_path)
        #im_B = Image.open(im_B_path)
        #W_A, H_A = im_A.size
        #W_B, H_B = im_B.size
        #pil_im = Image.open(r"C:\Users\lmorelli\Desktop\Luca\GitHub_3DOM\deep-image-matching\assets\example_mascotte\mascotte.jpg").resize((784, 784))
        #standard_im = np.array(pil_im)/255.
        #print(standard_im.shape)
        resized_image = cv2.resize(image, (784, 784))
        standard_im = np.array(resized_image)/255.
        #resized_image = cv2.resize(image, (784, 784))
        #standard_im = np.array(resized_image)/255.
        norm_image = self.normalizer(torch.from_numpy(standard_im).permute(2,0,1)).float().to(self._device)[None]
        batch = {"image": norm_image}
        #detections_A = detector.detect_dense(batch)
        detections_A = detector.detect(batch, num_keypoints = 1000)
        keypoints_A, P_A = detections_A["keypoints"], detections_A["confidence"]
        description_A = descriptor.describe_keypoints(batch, keypoints_A)["descriptions"]

        kpts = keypoints_A.cpu().detach().numpy()[0]
        des = description_A.cpu().detach().numpy()[0]

        kpts[:,0] =  ((kpts[:,0] + 1) * W / 2)
        kpts[:,1] =  ((kpts[:,1] + 1) * H / 2)
        feats = FeaturesDict(keypoints=kpts, descriptors=des.T)


        return feats

    def _frame2tensor(self, image: np.ndarray, device: str = "cuda"):
        """
        Convert a frame to a tensor.

        Args:
            image: The image to be converted
            device: The device to convert to (defaults to 'cuda')
        """
        if len(image.shape) == 2:
            image = image[None][None]
        elif len(image.shape) == 3:
            image = image.transpose(2, 0, 1)[None]
        return torch.tensor(image / 255.0, dtype=torch.float).to(device)