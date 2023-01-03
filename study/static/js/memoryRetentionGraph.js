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