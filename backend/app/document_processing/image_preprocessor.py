import cv2
import numpy as np
from pathlib import Path


class ImagePreprocessor:
    """
    OpenCV preprocessing pipeline for clinical evaluation sheets and photographs:
    - Auto-rotation / orientation correction
    - Deskewing via minAreaRect
    - Grayscale conversion and bilateral filtering for noise reduction
    - Adaptive thresholding & Otsu binarization
    """

    @staticmethod
    def load_image(image_path: str) -> np.ndarray:
        p = Path(image_path)
        if not p.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")
        img = cv2.imread(str(p))
        if img is None:
            raise ValueError("Failed to decode image. Corrupted or invalid image file.")
        return img

    @staticmethod
    def deskew(image: np.ndarray) -> np.ndarray:
        """Correct rotational skew using bounding box of text contours."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        # Invert colors: text white, background black
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Coordinates of all non-zero pixels
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return image
            
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Avoid extreme rotation if angle is small
        if abs(angle) < 0.5 or abs(angle) > 45:
            return image
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return rotated

    @staticmethod
    def preprocess_for_ocr(image: np.ndarray) -> dict:
        """
        Runs complete preprocessing pipeline:
        Returns:
            {
                "original": original image,
                "deskewed": deskewed image,
                "gray": grayscale image,
                "binary": adaptive thresholded image,
                "height": h,
                "width": w
            }
        """
        deskewed = ImagePreprocessor.deskew(image)
        gray = cv2.cvtColor(deskewed, cv2.COLOR_BGR2GRAY) if len(deskewed.shape) == 3 else deskewed
        # Bilateral filter reduces noise while keeping edges sharp
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        # Adaptive thresholding
        binary = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
        )
        (h, w) = deskewed.shape[:2]
        return {
            "deskewed": deskewed,
            "gray": gray,
            "binary": binary,
            "height": h,
            "width": w,
        }
