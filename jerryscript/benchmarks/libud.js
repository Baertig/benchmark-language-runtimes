var a = [];
var b = [];
var x = [];

var chkerr;

var SCALE_FACTOR = 1;

for (var i = 0; i < 20; i++) {
  a[i] = [];
  for (var j = 0; j < 20; j++) {
    a[i][j] = 0;
  }
  b[i] = 0;
  x[i] = 0;
}

function ludcmp(n) {
  var i, j, k;
  var w;
  var y = [];

  for (i = 0; i < n; i++) {
    for (j = i + 1; j <= n; j++) {
      w = a[j][i];
      if (i !== 0) {
        for (k = 0; k < i; k++) {
          w -= a[j][k] * a[k][i];
        }
      }
      a[j][i] = parseInt(w / a[i][i]);
    }

    for (j = i + 1; j <= n; j++) {
      w = a[i + 1][j];
      for (k = 0; k <= i; k++) {
        w -= a[i + 1][k] * a[k][j];
      }
      a[i + 1][j] = w;
    }
  }

  y[0] = b[0];
  for (i = 1; i <= n; i++) {
    w = b[i];
    for (j = 0; j < i; j++) {
      w -= a[i][j] * y[j];
    }
    y[i] = w;
  }

  x[n] = parseInt(y[n] / a[n][n]);
  for (i = n - 1; i >= 0; i--) {
    w = y[i];
    for (j = i + 1; j <= n; j++) {
      w -= a[i][j] * x[j];
    }
    x[i] = parseInt(w / a[i][i]);
  }

  return 0;
}

function verify_benchmark(res) {
  var x_ref = [0, 0, 1, 1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

  var match = true;
  for (var i = 0; i < 20; i++) {
    if (x[i] !== x_ref[i]) {
      match = false;
      break;
    }
  }

  return match && res === 0;
}

function benchmark() {
  var sf = SCALE_FACTOR;

  for (var sf_cnt = 0; sf_cnt < sf; sf_cnt++) {
    var i,
      j,
      n = 5;
    var w;

    for (i = 0; i <= n; i++) {
      w = 0;
      for (j = 0; j <= n; j++) {
        a[i][j] = i + 1 + (j + 1);
        if (i === j) {
          a[i][j] *= 2;
        }
        w += a[i][j];
      }
      b[i] = w;
    }

    chkerr = ludcmp(n);
  }

  return verify_benchmark(chkerr);
}

benchmark();
