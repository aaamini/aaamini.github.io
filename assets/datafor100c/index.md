---
layout: default
title: Datasets for 100c
---


<style>
ul {
  columns: 3;
  -webkit-columns: 3;
  -moz-columns: 3;
}
</style>

<h1>Datasets for 100c</h1>
<p>Datasets from the book by Abraham and Ledolter, borrowed from <a href="https://www.biz.uiowa.edu/faculty/jledolter/RegressionModeling/">this link</a>:</p>

<ul>
{% for file in site.static_files %}
  {% if file.extname == '.txt' %}
    <li><a href="{{ site.baseurl }}{{ file.path }}">{{ file.basename }}</a></li>
  {% endif %}
{% endfor %}
</ul>

