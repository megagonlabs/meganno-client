# Welcome to Labeler documentation
## Introduction
Data labeling is a key part of the machine learning (ML) life cycle. Relevant and high-quality labels can significantly improve the quality of models. However, labeling can be expensive and time-consuming, which means there is an opportunity for novel tools to reduce cost and burden. Labeler (also named [MEGAnno](https://megagon.ai/meganno_jupyter)) is our flexible, exploratory, efficient, and seamless labeling framework for NLP researchers and practitioners.

* Labeler is a framework consisting of customizable UI and programmatic interfaces, plus backend storage and management for your data, annotations, and auxiliary information.
* Labeler is with you throughout the entire life cycle of your annotation project, from early-stage exploration to analysis, project evolution, and large-scale deployment, meeting you where your everyday data science work takes place.
* Labeler provides a useful set of out-of-the-box “power tools” which give you extra leverage and reach. The tools could be easily extended to fit the special needs of projects.

Labeler provides 1) a client library with both interactive in-notebook UI widgets and Python programmatic interfaces, and 2) a back-end service that stores and manages all needed information with language-agnostic REST APIs. This is the documentatin for the client library, for instructions of setting up a service, please refer to the [service documentations](https://github.com/rit-git/labeler-service).

## Interactive Jupyter Widgets
Labeler’s annotation widget features 1) a table view to facilitate exploratory and batch labeling and 2) a more zoomed-in single view with more space for each data example, as in most existing labeling tools.

![Labeler's table view](assets/images/table.gif)
<br/><span style="color: gray;">*Table view of the annotation widget. Data examples are organized in a table for better exploration and comparison. Users can also search over, sort or filter on data and annotations.*</span>

![Labeler's single view](assets/images/single.gif)
<br/><span style="color: gray;">*Single view of the annotation widget showing one data example at a time. With more space, the single view is more suitable for span-level tasks like extraction.*</span>

Please see the [Getting Started](quickstart.md) page for setup instructions and the [Advanced Features](advanced.md) page for more cool features we provide.