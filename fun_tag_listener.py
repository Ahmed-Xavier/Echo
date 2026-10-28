#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
import subprocess
import time

class FunTagListener(Node):
    def __init__(self):
        super().__init__('fun_tag_listener')
        self.subscription = self.create_subscription(
            String,
            '/apriltag/instruction',
            self.listener_callback,
            10)
        self.last_trigger = 0
        self.get_logger().info('Fun Tag Listener active. Standing by for ID 10...')

    def listener_callback(self, msg):
        try:
            data = json.loads(msg.data)
            tag_id = data.get('tag_id')
            
            # Postcard Tag (ID 10 or ID 0 for testing)
            if (tag_id == 10 or tag_id == 0) and (time.time() - self.last_trigger > 10):
                self.get_logger().info('Postcard Tag detected! Capturing moment...')
                self.last_trigger = time.time()
                
                # The "Witty Observation" command
                obs = "🤖 Postcard from Sector Zero: I found a human trying to be productive. Or maybe just another cable. Hard to tell from this angle."
                
                # Trigger capture and send
                # Note: uses /dev/video8 based on our recent successful check
                postcard_path = os.path.expanduser(os.getenv("ECHO_POSTCARD_PATH", "~/echo_runtime/postcard.jpg"))
                telegram_id = os.getenv("TELEGRAM_ID", "")
                cmd = f'python3 -c "import cv2; cap = cv2.VideoCapture(8); [cap.read() for _ in range(10)]; ret, frame = cap.read(); cv2.imwrite(\\"{postcard_path}\\", frame); cap.release()" && openclaw message send --target telegram:{telegram_id} --message "{obs}" --media {postcard_path}'
                subprocess.run(cmd, shell=True)
                
                # Speak it too!
                voice_cmd = "python3 -c \"import os, requests, subprocess; vid=os.getenv('ELEVENLABS_VOICE_ID', 'JBFqnCBsd6RMkjVDRZzb'); key=os.getenv('ELEVENLABS_API_KEY', ''); headers={'xi-api-key': key, 'Content-Type': 'application/json'}; resp=requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}', json={'text': 'Cheese! Sending your postcard now.', 'model_id': 'eleven_multilingual_v2'}, headers=headers); open('/tmp/postcard_reply.mp3', 'wb').write(resp.content); subprocess.run(['ffplay', '-nodisp', '-autoexit', '/tmp/postcard_reply.mp3'])\""
                subprocess.run(voice_cmd, shell=True)

        except Exception as e:
            self.get_logger().error(f'Error processing tag: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = FunTagListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
