from setuptools import setup

package_name = 'robot_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/robot_controller']),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/ekf_launch.py',
            'launch/slam_launch.py',
        ]),
        ('share/' + package_name + '/config', [
            'ekf.yaml',
            'nav2_params.yaml',
            'slam_config.yaml',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ahmed-Xavier',
    maintainer_email='',
    description='Echo motor, encoder, IMU, and odometry ROS 2 nodes',
    license='MIT',
    entry_points={
        'console_scripts': [
            'motor_controller = robot_controller.motor_controller:main',
            'encoder_odometry = robot_controller.encoder_odometry:main',
            'esp32_encoder_odometry = robot_controller.esp32_encoder_odometry:main',
            'imu_node = robot_controller.imu_node:main',
        ],
    },
)
