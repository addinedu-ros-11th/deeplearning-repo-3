# fall_pipeline.py
import numpy as np
import torch

SEQ_LEN = 30

class FallDetectionPipeline:
    def __init__(self, pose, lstm, rule, device):
        self.pose = pose
        self.lstm = lstm
        self.rule = rule
        self.device = device

        self.seq_buffer = []
        self.bbox_buffer = []

    def process_frame(self, frame):
        result = self.pose.infer(frame)

        if result.keypoints is None or len(result.keypoints.xy) == 0:
            return None

        kpts = result.keypoints.xy[0].cpu().numpy()
        box = result.boxes.xyxy[0].cpu().numpy()

        self.seq_buffer.append(kpts)
        self.bbox_buffer.append(box)

        if len(self.seq_buffer) > SEQ_LEN:
            self.seq_buffer.pop(0)
            self.bbox_buffer.pop(0)

        if len(self.seq_buffer) < SEQ_LEN:
            return None

        seq = np.array(self.seq_buffer)
        x = torch.tensor(
            seq.reshape(1, SEQ_LEN, -1),
            dtype=torch.float32
        ).to(self.device)

        lstm_prob = self.lstm.infer(x)
        rule_prob = self.rule.infer(seq, self.bbox_buffer[-1])

        final_prob = 0.75 * lstm_prob + 0.25 * rule_prob

        return {
            "lstm_prob": lstm_prob,
            "rule_prob": rule_prob,
            "final_prob": final_prob,
            "label": "FALL" if final_prob > 0.30 else "NORMAL"
        }
