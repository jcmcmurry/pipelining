cl1 = 1;
Point(1) = {0, 0, 0, cl1};
Point(2) = {0, 1, 0, cl1};
Point(3) = {-1, 1, 0, cl1};
Point(4) = {1, 1, 0, cl1};
Point(5) = {1, 2, 0, cl1};
Point(6) = {-1, 2, 0, cl1};
Circle(1) = {3, 2, 1};
Circle(2) = {1, 2, 4};
Line(3) = {4, 5};
Line(4) = {5, 6};
Line(5) = {6, 3};
Line Loop(7) = {3, 4, 5, 1, 2};
Plane Surface(7) = {7};
