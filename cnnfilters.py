from __future__ import print_function
import scipy.signal as sig
import scipy.integrate as sint
from PIL import Image as img
import numpy as np
import os.path
import warnings

#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The MIT License (MIT)
Copyright (c) 2014 Ankit Aggarwal <ankitaggarwal011@gmail.com>
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import print_function
import scipy.signal as sig
import scipy.integrate as sint
from PIL import Image as img
import numpy as np
import os.path
import warnings

SUPPORTED_FILETYPES = (
    'jpeg', 'jpg', 'png', 'tiff', 'gif', 'bmp',
)

warnings.filterwarnings('ignore')  # Ignore trivial warnings


class PyCNN(object):
    """Image Processing with Cellular Neural Networks (CNN).
    Cellular Neural Networks (CNN) are a parallel computing paradigm that was
    first proposed in 1988. Cellular neural networks are similar to neural
    networks, with the difference that communication is allowed only between
    neighboring units. Image Processing is one of its applications. CNN
    processors were designed to perform image processing; specifically, the
    original application of CNN processors was to perform real-time ultra-high
    frame-rate (>10,000 frame/s) processing unachievable by digital processors.
    This python library is the implementation of CNN for the application of
    Image Processing.
    Attributes:
        n (int): Height of the image.
        m (int): Width of the image.
    """

    def __init__(self):
        """Sets the initial class attributes m (width) and n (height)."""
        self.m = 0  # width (number of columns)
        self.n = 0  # height (number of rows)

    def f(self, t, x, Ib, Bu, tempA):
        """Computes the derivative of x at t.
        Args:
            x: The input.
            Ib (float): System bias.
            Bu: Convolution of control template with input.
            tempA (:obj:`list` of :obj:`list`of :obj:`float`): Feedback
                template.
        """
        x = x.reshape((self.n, self.m))
        dx = -x + Ib + Bu + sig.convolve2d(self.cnn(x), tempA, 'same')
        return dx.reshape(self.m * self.n)

    def cnn(self, x):
        """Piece-wise linear sigmoid function.
        Args:
            x : Input to the piece-wise linear sigmoid function.
        """
        return 0.5 * (abs(x + 1) - abs(x - 1))

    # tempA: feedback template, tempB: control template
    def imageProcessing(self, inImg,
                        tempA, tempB, initialCondition, Ib, t):
        """Process the image with the input arguments.
        Args:
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
            tempA (:obj:`list` of :obj:`list`of :obj:`float`): Feedback
                template.
            tempB (:obj:`list` of :obj:`list`of :obj:`float`): Control
                template.
            initialCondition (float): The initial state.
            Ib (float): System bias.
            t (numpy.ndarray): A numpy array with evenly spaced numbers
                representing time points.
        """
        gray = inImg.convert('RGB')
        self.m, self.n = gray.size
        u = np.array(gray)
        u = u[:, :, 0]
        z0 = u * initialCondition
        Bu = sig.convolve2d(u, tempB, 'same')
        z0 = z0.flatten()
        tFinal = t.max()
        tInitial = t.min()
        if t.size > 1:
            dt = t[1] - t[0]
        else:
            dt = t[0]
        ode = sint.ode(self.f) \
            .set_integrator('vode') \
            .set_initial_value(z0, tInitial) \
            .set_f_params(Ib, Bu, tempA)
        while ode.successful() and ode.t < tFinal + 0.1:
            ode_result = ode.integrate(ode.t + dt)
        z = self.cnn(ode_result)
        out_l = z[:].reshape((self.n, self.m))
        out_l = out_l / (255.0)
        out_l = np.uint8(np.round(out_l * 255))
        # The direct vectorization was causing problems on Raspberry Pi.
        # In case anyone face a similar issue, use the below
        # loops rather than the above direct vectorization.
        # for i in range(out_l.shape[0]):
        #     for j in range(out_l.shape[1]):
        #         out_l[i][j] = np.uint8(round(out_l[i][j] * 255))
        out_l = img.fromarray(out_l)
        return out_l

    # general image processing for given templates
    def generalTemplates(self,
                         inImg,
                         name='Image processing',
                         tempA_A=[[0.0, 0.0, 0.0],
                                  [0.0, 0.0, 0.0],
                                  [0.0, 0.0, 0.0]],
                         tempB_B=[[0.0, 0.0, 0.0],
                                  [0.0, 0.0, 0.0],
                                  [0.0, 0.0, 0.0]],
                         initialCondition=0.0,
                         Ib_b=0.0,
                         t=np.linspace(0, 10.0, num=2)):
        """Validate and process the image with the input arguments.
        Args:
            name (str): The name of the template.
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
            tempA_A (:obj:`list` of :obj:`list`of :obj:`float`): Feedback
                template.
            tempB_B (:obj:`list` of :obj:`list`of :obj:`float`): Control
                template.
            initialCondition (float): The initial state.
            Ib_b (float): System bias.
            t (numpy.ndarray): A numpy array with evenly spaced numbers
                representing time points.
        """
        return self.imageProcessing(inImg,
                             np.array(tempA_A),
                             np.array(tempB_B),
                             initialCondition,
                             Ib_b,
                             t)

    def edgeDetection(self, inImg):
        """Performs Edge Detection on the input image.
        The output is a binary image showing all edges of the input image in
        black.
        A = [[0.0 0.0 0.0],
             [0.0 1.0 0.0],
             [0.0 0.0 0.0]]
        B = [[−1.0 −1.0 −1.0],
             [−1.0 8.0 −1.0],
             [−1.0 −1.0 −1.0]]
        z = −1.0
        Initial state = 0.0
        Args:
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
        """
        name = 'Edge detection'
        tempA = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
        tempB = [[-1.0, -1.0, -1.0], [-1.0, 8.0, -1.0], [-1.0, -1.0, -1.0]]
        Ib = -1.0
        # num refers to the number of samples of time points from start = 0 to
        # end = 10.0
        t = np.linspace(0, 10.0, num=2)
        # some image processing methods might require more time point samples.
        initialCondition = 0.0
        return self.generalTemplates(
            inImg,
            name,
            tempA,
            tempB,
            initialCondition,
            Ib,
            t)

    def grayScaleEdgeDetection(self, inImg):
        """Performs Gray-scale Edge Detection on the input image.
        The output is a Gray-scale image showing an edge map of the input
        image in black.
        A = [[0.0 0.0 0.0],
             [0.0 2.0 0.0],
             [0.0 0.0 0.0]]
        B = [[−1.0 −1.0 −1.0],
             [−1.0 8.0 −1.0],
             [−1.0 −1.0 −1.0]]
        z = −0.5
        Initial state = 0.0
        Args:
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
        """
        name = 'Grayscale edge detection'
        tempA = [[0.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 0.0]]
        tempB = [[-1.0, -1.0, -1.0], [-1.0, 8.0, -1.0], [-1.0, -1.0, -1.0]]
        Ib = -0.5
        t = np.linspace(0, 1.0, num=101)
        initialCondition = 0.0
        return self.generalTemplates(
            inImg,
            name,
            tempA,
            tempB,
            initialCondition,
            Ib,
            t)

    def cornerDetection(self, inImg):
        """Performs Corner Detection on the input image.
        The output is a binary image where black pixels represent the convex
        corners of objects in the input image.
        A = [[0.0 0.0 0.0],
             [0.0 1.0 0.0],
             [0.0 0.0 0.0]]
        B = [[−1.0 −1.0 −1.0],
             [−1.0 4.0 −1.0],
             [−1.0 −1.0 −1.0]]
        z = −5.0
        Initial state = 0.0
        Args:
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
        """
        name = 'Corner detection'
        tempA = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
        tempB = [[-1.0, -1.0, -1.0], [-1.0, 4.0, -1.0], [-1.0, -1.0, -1.0]]
        Ib = -5.0
        t = np.linspace(0, 10.0, num=11)
        initialCondition = 0.0
        return self.generalTemplates(
            inImg,
            name,
            tempA,
            tempB,
            initialCondition,
            Ib,
            t)

    def diagonalLineDetection(self, inImg):
        """Performs Diagonal Line-Detection on the input image.
        The output is a binary image representing the locations of diagonal
        lines in the input image.
        A = [[0.0 0.0 0.0],
             [0.0 1.0 0.0],
             [0.0 0.0 0.0]]
        B = [[−1.0 0.0 −1.0],
             [0.0 1.0 0.0],
             [1.0 0.0 −1.0]]
        z = −4.0
        Initial state = 0.0
        Args:
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
        """
        name = 'Diagonal line detection'
        tempA = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
        tempB = [[-1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, -1.0]]
        Ib = -4.0
        t = np.linspace(0, 0.2, num=101)
        initialCondition = 0.0
        return self.generalTemplates(
            inImg,
            name,
            tempA,
            tempB,
            initialCondition,
            Ib,
            t)

    def inversion(self, inImg):
        """Performs Inversion (Logic NOT) on the input image.
        A = [[0.0 0.0 0.0],
             [0.0 1.0 0.0],
             [0.0 0.0 0.0]]
        B = [[0.0 0.0 0.0],
             [1.0 1.0 1.0],
             [0.0 0.0 0.0]]
        z = −2.0
        Initial state = 0.0
        Args:
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
        """
        name = 'Inversion'
        tempA = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
        tempB = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]]
        Ib = -2.0
        t = np.linspace(0, 10.0, num=101)
        initialCondition = 0.0
        return self.generalTemplates(
            inImg,
            name,
            tempA,
            tempB,
            initialCondition,
            Ib,
            t)

    def optimalEdgeDetection(self, inImg):
        """Performs Optimal Edge Detection on the input image.
        A = [[0.0 0.0 0.0],
             [0.0 0.0 0.0],
             [0.0 0.0 0.0]]
        B = [[-0.11 0.0 0.11],
             [-0.28.0 0.0 0.28],
             [-0.11 0.0 0.11]]
        z = 0.0
        Initial state = 0.0
        Args:
            inputLocation (str): The string path for the input image.
            outputLocation (str): The string path for the output processed
                image.
        """
        name = 'Optimal Edge Detection'
        tempA = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        tempB = [[-0.11, 0.0, 0.11], [-0.28, 0.0, 0.28], [-0.11, 0.0, 0.11]]
        Ib = 0.0
        t = np.linspace(0, 10.0, num=101)
        initialCondition = 0.0
        return self.generalTemplates(
            inImg,
            name,
            tempA,
            tempB,
            initialCondition,
            Ib,
            t)