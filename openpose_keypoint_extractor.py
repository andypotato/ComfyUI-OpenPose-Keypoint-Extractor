from nodes import MAX_RESOLUTION

class OpenPoseKeyPointExtractor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "pose_keypoint": ("POSE_KEYPOINT",),
                "image_width": ("INT", { "min": 0, "max": MAX_RESOLUTION }),
                "image_height": ("INT", { "min": 0, "max": MAX_RESOLUTION }),
                "points_list": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "person_number": ("INT", { "default": 0 }),
                "min_confidence": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "keypoint_padding": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT")
    RETURN_NAMES = ("x", "y", "width", "height")
    FUNCTION = "box_keypoints"
    CATEGORY = "utils"

    def get_keypoint_from_list(self, list, item):
        idx_x = item*3
        idx_y = idx_x + 1
        idx_conf = idx_y + 1
        # prevent out of bounds errors
        if idx_conf >= len(list):
            return (0.0, 0.0, 0.0)
        return (list[idx_x], list[idx_y], list[idx_conf])

    def box_keypoints(self, pose_keypoint, image_width, image_height, points_list,
                      person_number=0, min_confidence=0.5, keypoint_padding=0):
        points_we_want = [int(element) for element in points_list.split(",")]

        min_x = MAX_RESOLUTION
        min_y = MAX_RESOLUTION
        max_x = 0
        max_y = 0

        for element in points_we_want:
            (x,y,z) = self.get_keypoint_from_list(pose_keypoint[0]["people"][person_number]["pose_keypoints_2d"], element)

            # only include points that meet the minimum confidence
            if z >= min_confidence:
                if x < min_x: min_x = x
                if y < min_y: min_y = y
                if x > max_x: max_x = x
                if y > max_y: max_y = y

        # in case no valid keypoints were found return the full image
        if min_x == MAX_RESOLUTION:
            return (0, 0, image_width, image_height)

        # 1. Calculate the original box in pixels
        box_x1 = int(min_x * image_width)
        box_y1 = int(min_y * image_height)
        box_x2 = int(max_x * image_width)
        box_y2 = int(max_y * image_height)
        
        # 2. Apply padding
        padded_x1 = box_x1 - keypoint_padding
        padded_y1 = box_y1 - keypoint_padding
        padded_x2 = box_x2 + keypoint_padding
        padded_y2 = box_y2 + keypoint_padding

        # 3. Clamp the coordinates to the image boundaries
        final_x = max(0, padded_x1)
        final_y = max(0, padded_y1)
        final_x2 = min(image_width, padded_x2)
        final_y2 = min(image_height, padded_y2)
        
        # 4. Calculate final width and height from the clamped coordinates
        final_width = final_x2 - final_x
        final_height = final_y2 - final_y
                
        return (final_x, final_y, final_width, final_height)

class CanvasPositioner:
    @classmethod
    def INPUT_TYPES(s):
        # The list of anchor points for the dropdown menu
        anchor_points = [
            "center", "top-center", "bottom-center", "left-center", "right-center",
            "top-left", "top-right", "bottom-left", "bottom-right"
        ]
        return {
            "required": {
                "content_width": ("INT", {"default": 512, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "content_height": ("INT", {"default": 512, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "target_canvas_width": ("INT", {"default": 1024, "min": 1, "max": MAX_RESOLUTION, "step": 8}),
                "target_canvas_height": ("INT", {"default": 1024, "min": 1, "max": MAX_RESOLUTION, "step": 8}),
                "anchor_point": (anchor_points,),
                "offset_x": ("INT", {"default": 0, "min": -MAX_RESOLUTION, "max": MAX_RESOLUTION, "step": 1}),
                "offset_y": ("INT", {"default": 0, "min": -MAX_RESOLUTION, "max": MAX_RESOLUTION, "step": 1}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("pos_x", "pos_y")
    FUNCTION = "calculate_position"
    CATEGORY = "utils" # You can place it in the same category or a new one

    def calculate_position(self, content_width, content_height, target_canvas_width, target_canvas_height, anchor_point, offset_x, offset_y):
        # Horizontal alignment
        if "left" in anchor_point:
            base_x = 0
        elif "right" in anchor_point:
            base_x = target_canvas_width - content_width
        else: # center
            base_x = (target_canvas_width - content_width) // 2
            
        # Vertical alignment
        if "top" in anchor_point:
            base_y = 0
        elif "bottom" in anchor_point:
            base_y = target_canvas_height - content_height
        else: # center
            base_y = (target_canvas_height - content_height) // 2

        pos_x = base_x + offset_x
        pos_y = base_y + offset_y

        return (pos_x, pos_y)

NODE_CLASS_MAPPINGS = {
    "Openpose Keypoint Extractor": OpenPoseKeyPointExtractor,
    "Canvas Positioner": CanvasPositioner,
}
