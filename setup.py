from setuptools import setup, find_packages

setup(
    name="deepseek-wrapper",
    version="0.1.0",
    description="Python wrapper for DeepSeek LLM API (local and remote)",
    author="TM Hospitality Strategies",
    author_email="email@info.com",
    url="https://github.com/TMHSDigital/deepseek-wrapper",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "httpx>=0.27.0",
        "python-dotenv>=1.0.1",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0",
        "Operating System :: OS Independent",
    ],
) 