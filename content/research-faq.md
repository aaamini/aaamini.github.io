---
title: Research FAQ
permalink: /research-faq
---
If you are thinking of sending me an email inquiring about research opportunities, please consider including the following (also please let me know of any typos on this page):

## If you are an undergraduate student ...
The solution to the following problem:
- Assume that we are given two $m \times n$ real-valued matrices $A$ and $B$, and we know that $B$ can be obtained by permuting the rows and columns of $A$ in some unknown fashion. Describe an algorithm for recovering the row and column permutations that match $A$ to $B$. That is, the algorithm is supposed to find $\pi : \{1,\dots,m\} \to \{1,\dots,m\}$ and $\sigma: \{1,\dots,n\} \to \{1,\dots,n\}$ such that

  $$A_{\pi(i), \sigma(j)} = B_{ij}, \quad \text{for all $i$ and $j$}.$$

  Write a few lines of code in the language of your choice (R, MATLAB, Python or C++ are preferred) to implement your algorithm. Then, apply your algorithm to the following two matrices and let me know what the row permutation $\pi$ is: [Matrix A](/assets/csv/A.csv) and [Matrix B](/assets/csv/B.csv). Include the description of your algorithm and your code in your response. The more computationally efficient your algorithm, the better.

## If you are a graduate student ...
- Whether you are more interested in the applied problems or the theory.
- Whether you have started reading research papers. If so, tell me about one or two recent papers that you found interesting. (This should exclude any paper that I am a co-author of.)
- The answer to one of the following problems:

    * Let $X_1,\dots,X_n$ be i.i.d. zero mean random variables with finite moments of all order. How fast does the third **absolute** moment of $S_n = \sum_{i=1}^n X_i$ grow as a function of $n$?

    *   Suppose that we have two parametric statistical models $\{P_\theta\}_\theta$ and $\{Q_\alpha\}_{\alpha}$ for a particular dataset. You can think of $\{P_\theta\}$ as continuous distributions with well-behaved densities parametrized by $\theta$, and similarly for $\{Q_\alpha\}$. Suppose that we fit these two models to the data. How do we determine which model is better? Consider the case where we have some real data at hand, so describe a procedure that we can implement in practice. The more generally applicable the procedure, the better.

## Coding Challenge
- Re-implement the function `compute_block_sums` [written in R here](https://github.com/aaamini/nett/blob/master/R/estimate.R), in C++ using `RcppArmadillo`, and make it as fast as you can. Benchmark your function against the aforementioned R implementation by generating samples from a DCSBM on n = 5000 nodes. Refer to the [`nett` package](https://aaamini.github.io/nett/) documentation for how to do that.
