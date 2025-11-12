var SCALE_FACTOR = 100;

var sum = 0;
for (var i = 0; i <= SCALE_FACTOR; i++) {
  sum += i;
}

var expectedSum = (SCALE_FACTOR * (SCALE_FACTOR + 1)) / 2;

sum === expectedSum;
