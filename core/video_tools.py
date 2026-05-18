import cv2
import numpy as np

class VideoTools:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video at {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def get_frame(self, frame_idx: int):
        """Returns the frame (numpy array) at the specified index."""
        if frame_idx < 0 or frame_idx >= self.total_frames:
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        return frame if ret else None

    def find_event_frame(self, start_idx=0, end_idx=None, diff_threshold=30) -> int:
        """
        Scans frames for motion (difference) to identify the 'event' (e.g., stump hit).
        Returns the frame index of the maximum motion peak.
        This is a rudimentary implementation for the MVP.
        """
        if end_idx is None:
            end_idx = self.total_frames
        
        max_diff = 0
        event_frame_idx = start_idx
        
        # Read the first frame
        prev_frame = self.get_frame(start_idx)
        if prev_frame is None:
            return start_idx
            
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        
        # We step by 2 frames to speed up processing for the MVP
        for i in range(start_idx + 2, end_idx, 2):
            curr_frame = self.get_frame(i)
            if curr_frame is None:
                break
                
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            # Calculate absolute difference
            diff = cv2.absdiff(prev_gray, curr_gray)
            # Threshold to get significant changes
            _, thresh = cv2.threshold(diff, diff_threshold, 255, cv2.THRESH_BINARY)
            
            # Count the number of non-zero pixels as a measure of motion
            motion_score = np.sum(thresh) / 255
            
            if motion_score > max_diff:
                max_diff = motion_score
                event_frame_idx = i
                
            prev_gray = curr_gray
            
        return event_frame_idx

    def get_frame_range(self, center_frame_idx: int, num_before=2, num_after=2, step=1):
        """
        Yields a list of frames around the center_frame_idx with a configurable step interval.
        """
        frames = []
        
        # Before frames
        for i in range(num_before, 0, -1):
            idx = center_frame_idx - (i * step)
            if idx >= 0:
                f = self.get_frame(idx)
                if f is not None:
                    frames.append((idx, f))
                    
        # Center frame
        f = self.get_frame(center_frame_idx)
        if f is not None:
            frames.append((center_frame_idx, f))
            
        # After frames
        for i in range(1, num_after + 1):
            idx = center_frame_idx + (i * step)
            if idx < self.total_frames:
                f = self.get_frame(idx)
                if f is not None:
                    frames.append((idx, f))
                    
        return frames

    def release(self):
        self.cap.release()

