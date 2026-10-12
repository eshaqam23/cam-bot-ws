from setuptools import find_packages, setup

package_name = "cam_bot_skeleton"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/skeleton.launch.py", "launch/color_detector.launch.py"]),
        (f"share/{package_name}/config", ["config/params.yaml", "config/color_detector.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="user@example.com",
    description="Minimal Python skeleton package for the cam bot workspace.",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "skeleton_node = cam_bot_skeleton.skeleton_node:main",
            "color_detector = cam_bot_skeleton.color_detector_node:main",
        ],
    },
)
