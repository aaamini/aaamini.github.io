---
title: 'Fun with numpy broadcasting'
date: 2022-03-30
---
---
Have you ever heard of the saying "It is not a bug. It is a feature."? If not, by the end of this post you will have a good idea what it means. We will see an example where a piece of code runs perfectly without error but does something completely different from what you might think it does (unless you are one of `numpy` designers!)

## Simple regression
Let's generate some noisy data:

```python
import numpy as np
from sklearn.linear_model import LinearRegression

np.random.seed(34)
x = np.random.rand(50,1)
noise = 0.5*np.random.randn(50)
mu = 2*x - 1
y = mu + noise
```

We next fit a linear regression model $$y \sim \beta_0 + \beta_1 x$$ and check the resulting [coefficient of determination a.k.a. the $$R^2$$](https://en.wikipedia.org/wiki/Coefficient_of_determination):

```python
model = LinearRegression(fit_intercept=True).fit(x,y)
model.score(x,y)
```




    1.0



After congradulating ourselves on the perfect fit to noisy data, it occurs to us that this is perhaps not what should have happened.


## Wonders of broadcasting
Let's check the dimensions of $$y$$:

```python
y.shape
```




    (50, 50)



OK, this wasn't the intension. We generated a $$50 \times 1$$ vector $$x$$ and passed it through an affine transformation, $$x \mapsto 2 x + 1$$, the output of which `mu` should still be a $$50 \times 1$$ vector. Then, we added a $$50  \times 1$$ `noise` vector to `mu` get $$y$$. So, if all went according to plan, we would have a $$50 \times 1$$ vector for $$y$$, not a $$50 \times 50$$ matrix. Let's check the shape of `noise`:

```python
noise.shape
```




    (50,)



This is a 50-element 1D `numpy` array. Close enough to pass as a $$50 \times 1$$ vector, isn't it? No! 

A $$50 \times 1$$ object like `mu` is a 2D `numpy` array and different from the 1D 50-element array `noise`. When we add them, `numpy` performs something called [broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html). To quote `numpy` documentation:
> When operating on two arrays, NumPy compares their shapes element-wise. It starts with the trailing (i.e. rightmost) dimensions and works its way left. Two dimensions are compatible when
> 1. they are equal, or
> 2. one of them is 1

Since `noise` is a 1D array, it has a single dimension, while `mu` has 2 dimensions. So they are aligned like this (alignment occurs from the right)

$$
\begin{matrix}
\text{mu:} & 50 & 1 \\
\text{noise:} & & 50
\end{matrix}
$$

and since the dimensions are compatible according to rule 2 above, the dimension with size 1 is "stretched or “copied” to match the other". That is a $$50 \times 50$$ matrix is created whose columns are repeated copies of `mu` and to each of these columns one element of `noise` is added: 

$$
\begin{bmatrix}
    \text{mu} + \text{noise}[0] & \text{mu} + \text{noise}[1] & \cdots & \text{mu} + \text{noise}[49]
\end{bmatrix}
$$

That is how out of two (essentially) vectors, we end up creating a matrix.

# A bit of statistics
OK. But why did we get a perfect $$R^2$$? You may want to pause here and think about it yourself.

***
If you followed so far, you notice that `noise` in our code is really not noise. We are basically adding a constant to each vector `mu`, so it effectively produces a respnse vector $$y$$ from a noiseless linear model on $$x$$ with the modified intercept $$-1  +$$ `noise`[j]. The rest is linear algebra. Fitting a linear model to a noiseless data of the form $$y = \beta_0' + \beta_1 x$$ produces a perfect fit. `sklearn.linear_model` acutally solves 50 of these perfect regressions, one for each column of that $$50 \times 50$$ matrix and reports [the average $$R^2$$](https://scikit-learn.org/stable/modules/generated/sklearn.multioutput.MultiOutputRegressor.html#sklearn.multioutput.MultiOutputRegressor.score) across those 50 problems:
> The  score used when calling score on a regressor uses multioutput='uniform_average' from version 0.23 to keep consistent with default value of r2_score. 

Since all these regressions have $$R^2=1$$, the average is still 1. 

Can we check to be sure? Yes. Let's look at

```python
model.intercept_
```


    array([-1.57147241, -0.89209023, -0.5371968 , -0.7963978 , -0.72115687,
           -1.27266215, -0.89665649, -1.32252765, -1.2642981 , -0.58057429,
           -1.65012604, -1.04847361, -0.89424701, -0.89050757, -1.73198845,
           -0.43596676, -0.2968391 , -1.06814484, -1.12911504, -0.96785297,
           -1.66824967, -0.73128158, -0.75711398, -1.00058578, -0.72238412,
           -1.30673187, -0.32309401, -0.10754156, -1.87670833, -1.15763191,
           -0.58670268, -1.10795688, -1.29891249, -0.90241915, -0.2034093 ,
           -1.00095005, -1.04258695, -0.3036957 , -1.06679342, -0.66243987,
           -1.06949021, -0.81706503, -1.33958021,  0.01017578, -0.63461253,
           -0.0683105 , -1.10392489, -1.25071897, -1.02860888, -1.39722975])



which should be equal to `noise` - 1 (again try to justify this for yourself)

```python
noise - 1
```




    array([-1.57147241, -0.89209023, -0.5371968 , -0.7963978 , -0.72115687,
           -1.27266215, -0.89665649, -1.32252765, -1.2642981 , -0.58057429,
           -1.65012604, -1.04847361, -0.89424701, -0.89050757, -1.73198845,
           -0.43596676, -0.2968391 , -1.06814484, -1.12911504, -0.96785297,
           -1.66824967, -0.73128158, -0.75711398, -1.00058578, -0.72238412,
           -1.30673187, -0.32309401, -0.10754156, -1.87670833, -1.15763191,
           -0.58670268, -1.10795688, -1.29891249, -0.90241915, -0.2034093 ,
           -1.00095005, -1.04258695, -0.3036957 , -1.06679342, -0.66243987,
           -1.06949021, -0.81706503, -1.33958021,  0.01017578, -0.63461253,
           -0.0683105 , -1.10392489, -1.25071897, -1.02860888, -1.39722975])



Can you guess what `model.coef_` would be? Note that in `sklearn.linear_model`, the intercept and regression parameters corresponding to nontrivial predictors/features are reported in different fields (`intercept_` versus `coef_`.).
