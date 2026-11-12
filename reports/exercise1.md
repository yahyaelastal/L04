# Bug reports for exercise1.py

Line: 3  
Problem: The docstring says "true for even numbers", but the function returns `n % 2 == 1`, which is true for odd numbers, not even ones.  
Example: is_even(4) returns False, but it should return True since 4 is even.  
Fix: Change `n % 2 == 1` to `n % 2 == 0`

Line: 8  
Problem: The docstring says "area of a rectangle", but the function returns `width + height`, which is the perimeter, not the area.  
Example: rectangle_area(4, 5) returns 9, but the correct area should be 20.  
Fix: Change `return width + height` to `return width * height`

Line: 12  
Problem: The docstring says "twice the number n", but the function returns `n + 2`, which adds 2, not doubles the number.  
Example: double(5) returns 7, but twice 5 is 10.  
Fix: Change `return n + 2` to `return n * 2`
