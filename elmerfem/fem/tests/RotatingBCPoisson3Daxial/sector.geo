c1 = 0.05;
Point(1) = {0, 0, 0, c1};
Point(2) = {1, 0, 0, c1};
Point(3) = {0, 1, 0, c1};
Line(1) = {1, 2};
Line(2) = {1, 3};
Circle(3) = {3, 1, 2};
Line Loop(5) = {3, -1, 2};
Plane Surface(5) = {5};
