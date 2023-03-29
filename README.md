# VisGrader: Automatic Grading of D3 Visualizations

[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT)
[![arXiv](https://img.shields.io/badge/arXiv-2110.11227-b3131b.svg)](https://arxiv.org/abs/2110.11227)


| ![crown_jewel](https://user-images.githubusercontent.com/683979/228333301-93f9c889-3687-4813-b29e-73cba408596f.png) |
| --- |



# Development

Clone or download this repository:

`git clone git@github.com:poloclub/visgrader.git`

Install the dependencies

`pip install -r requirements.txt`

Run the auto-grader example with: 

`./local_run_autograder`

Then view the graded results in `/sample/results.json`

To view the sample visualization, run a server in the `submission/` directory using;

`python -m http.server 3000 &`

Then navigate to `http://localhost:3000/submision.html`

# Credits
Led by [Matthew Hull](https://matthewdhull.github.io), VisGrader is a result of a collaboration between the [Polo Club of Data Science](https://poloclub.github.io) and Teaching Assistants from [CSE 6242 Data and Visual Analytics](https://poloclub.github.io/#cse6242) at Georgia Tech. VisGrader has been created by [Matthew Hull](https://matthewdhull.github.io), Vivian Pednekar, Hannah Murray, Nimisha Roy, Emmanuel Tung, Susanta Routray, Connor Guerin, Justin Chen, [Zijie J. Wang](https://zijie.wang), [Seongmin Lee](https://ligi214.github.io), [Mahdi Roozbahani](https://mahdi-roozbahani.github.io), and [Duen Horng Chau](https://poloclub.github.io/polochau/).

# Citation
To learn more about VisGrader, please read our preliminary two-page [poster paper](https://arxiv.org/abs/2110.11227) and [poster](https://poloclub.github.io/papers/21-vis-autograde-poster.pdf) presented at IEEE VIS 2021. Thanks!

```latex
@inproceedings{hull2021autogradeviz,
      title={Towards Automatic Grading of D3.js Visualizations},
      author={Matthew Hull, Connor Guerin, Justin Chen, Susanta Routray, Duen Horng (Polo) Chau},
      booktitle = {IEEE Visualization Conference (VIS), Poster},
      year={2021}}
```
