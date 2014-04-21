from scipy import interpolate
import numpy as np

#Dataset 3 Benchmark
#NearestPowerCurveInterpolator -> 0:01:18.958000
#IndexPowerCurveInterpolator -> 0:00:31.208000
#DictPowerCurveInterpolator -> 0:00:28.299000
#LinearPowerCurveInterpolator -> 0:01:42.443000

class LinearPowerCurveInterpolator:

    def __init__(self, x, y):

        self.interpolator = interpolate.interp1d(x, y, kind='linear')

    def __call__(self, x):
        return self.interpolator(x)

class DictPowerCurveInterpolator:

    def __init__(self, x, y):

        xStart = self.round(min(x))
        xEnd = self.round(max(x))
        
        xStep = 0.01
        steps = int((xEnd - xStart) / xStep) + 1

        self.points = {}
        interpolator = LinearPowerCurveInterpolator(x, y)
            
        for xp in np.linspace(xStart, xEnd, steps):
            x = self.round(xp)
            self.points[x] = interpolator(x)

    def __call__(self, x):
        return self.points[self.round(x)]

    def round(self, x):
        return round(x, 2)
		
class IndexPowerCurveInterpolator:

    def __init__(self, x, y):

        xStart = min(x)
        xEnd = max(x)

        xStep = 0.01
        self.oneOverXStep = 1.0 / xStep

        steps = int(xEnd / xStep) + 1

        self.points = []
        interpolator = interpolate.interp1d(x, y, kind='linear')

        for x in np.linspace(0.0, xEnd, steps):
            if x < xStart:
                self.points.append(0.0)
            else:
                self.points.append(interpolator(x))

    def __call__(self, x):
        index = int(round(x * self.oneOverXStep, 0))
        return self.points[index]

    def round(self, x):
        return round(x, 2)

class NearestPowerCurveInterpolator:

    def __init__(self, x, y):

        xStart = min(x)
        xEnd = max(x)
        xStep = 0.01
        steps = int(xEnd / xStep) + 1

        xp = []
        yp = []
        
        interpolator = interpolate.interp1d(x, y, kind='linear')

        for x in np.linspace(xStart, xEnd, steps):
            
            if x < xStart:
                y = 0.0
            else:
                y = interpolator(x)

            xp.append(x)
            yp.append(y)                

        self.interpolator = interpolate.interp1d(xp, yp, kind='nearest')
        
    def __call__(self, x):
        return self.interpolator(x)
