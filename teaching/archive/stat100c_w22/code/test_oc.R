data <- read.table("https://www.biz.uiowa.edu/faculty/jledolter/RegressionModeling/Data/Chapter1/contraceptive.txt")

data <- matrix( as.numeric(as.matrix(data[-1,])), nrow=10)

temp <- NULL
for (g in 1:5) {
  temp2 <- as.data.frame(data[,(g-1)*2+(1:2)])
  colnames(temp2) <- c("y","z")
  
  for (i in 1:5) {
    var_name <- paste("x",i,sep="")
    if (i==g) 
      temp2[var_name] = 1
    else
      temp2[var_name] = 0
  }
  
  temp <- rbind(temp, temp2)
}

y <- as.vector(temp[,1])
(X <- as.matrix(temp[,-1]))



beth <- solve(t(X) %*% X) %*% t(X) %*% y
muh <- X %*% beth
e <- y - muh

(sse_full <- t(e) %*% e)

Xt <- cbind(X[,1],1)
beth_A <- solve(t(Xt) %*% Xt) %*% t(Xt) %*% y
muh_A <- Xt %*% beth_A
e_A <- y - muh_A

(sse_A <- t(e_A) %*% e_A)

