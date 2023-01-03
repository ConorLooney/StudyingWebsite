function drawMemoryRetentionGraph(threshold, steepness, change) {
    // T = times studied
    // t = time since last studied
    function calc(T, t) {
        var memoryRetention = Math.pow(Math.E, -steepness * (Math.pow(change, T) * t));
        if (memoryRetention < threshold) {
            t = t - Math.log(threshold) / (-steepness * (Math.pow(change, T)));
            return calc(T + 1, t);
        }
        return [T, memoryRetention];
    }

    function forgettingCurveFunc(x) {
        var timesStudied = 0;
        [timesStudied, y] = calc(timesStudied, x);
        return y;
    }

    var board = JXG.JSXGraph.initBoard('jxgbox', {
        boundingbox: [-7, 1, 100, -0.2],
        axis: true,
        showcopyright: false,
    });

    board.update();

    var forgettingCurve = board.create('functiongraph', [forgettingCurveFunc]);

    var x = 0;
    let last = 0;
    while (x < 1000) {
        var timesStudied = 0;
        [timesStudied, y] = calc(timesStudied, x);
        if (timesStudied > last) {
            var line = board.create('line', [[x, 1], [x, 0]],
            {
                color: 'black'
            }
            );
        }
        last = timesStudied;
        x += 0.1;
    }
}

function updateGraph() {
    // get values 
    let threshold = document.getElementById("spaced_repetition_threshold").value;
    let steepness = document.getElementById("spaced_repetition_steepness_constant").value;
    let change = document.getElementById("spaced_repetition_change_constant").value;

    // validate values
    let valid = true;

    threshold = Number(threshold);
    if (isNaN(threshold)) {
        valid = false;
    }
    steepness = Number(steepness);
    if (isNaN(steepness)) {
        valid = false;
    }
    change = Number(change);
    if (isNaN(change)) {
        valid = false;
    }

    if (!valid) {
        return;
    }

    if (threshold <= 0 || threshold >= 1) {
        valid = false;
    }

    if (change <= 0 || change >= 1) {
        valid = false;
    }

    // valid ranges for steepness is undecided
    // TODO get valid ranges for steepness

    // only draw if valid
    if (valid) {
        drawMemoryRetentionGraph(threshold, steepness, change)
    }
}