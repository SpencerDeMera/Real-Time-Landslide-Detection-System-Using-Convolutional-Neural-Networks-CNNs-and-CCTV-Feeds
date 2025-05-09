# LandslideLens
**All-In-One Landslide Detection Systems**
<br>
**Status: Version 1.0.0 Complete**

### Author: Spencer DeMera

- EGEC 597 - Project
- California State University Fullerton

## Project Background
  As of recent, the accurate prediction and/or prompt detection of landslides has become of larger interest within the field of machine learning. Extensive research has been conducted primarily within the fields of landslide prediction and aerial detection, while prompt real-time detection has had minimal advancement. Recent advancement in machine learning, especially in the sub-field of computer vision have opened a wide range of opportunities for the development of relatively small but potent models attuned specifically for accurate real-time detection. The chosen model architecture of the proposed project is a Convolutional Neural Network based primarily for its proven effectiveness at both image and video analysis. By building a CNN and training it on a specially curated dataset of images that are sourced from highway live feeds (with the addition of landslide laden examples) the proposed system can easily identify landslide events or other such anomalies that differ from “normal” traffic conditions. Additionally, integrating this technology into a desktop application available for Windows will allow for the easy deployment of centralized landslide monitoring and management. Users responsible for system monitoring are also provided the tools to control and customize the detection process alongside the aid of supplementary data such as localized severe weather alerts. 

## General Application Methodology
  To implement the detection system, a CNN was developed using Python and the deep learning library Keras as a base. Meanwhile the physical desktop application was originally built with Django as a Model View Controller (MVC) based web application which was then packaged into a desktop application using Electron.js. While functionality can be accomplished as a web application, a desktop application was deemed more suitable for a system that would be regularly running image analysis tasks via Python. As a whole, project development was split into three separate phases; data collection, model design / training, and application development. These three phases culminated in the final product that serves as a rough starting point or base for a system that can potentially find use with many state agencies and integrated response systems. 

## Tools & Technologies Used
* Python
* PyTorch
* Keras
* Javascript
* HTML5
* CSS3
* Django
* Electron.js
* Google Colab
