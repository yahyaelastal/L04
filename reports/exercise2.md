# Bug reports for exercise2.py

Line: 3
Problem: "True if the grade is 5 or more" says "or more", which means >= 5, but the code uses > 5, which excludes 5. For example, if grade is 5, the function returns False when it should return True.
Fix: return grade >= 5

Line: 8
Problem: "At least 8 characters and at least one digit" requires "at least 8 characters", which means >= 8, but the code uses > 8. For example, a password of length 8 should be valid, but the function returns False because it checks len(password) > 8.
Fix: return len(password) >= 8 and any(c.isdigit() for c in password)

Line: 12
Problem: "x, limited to the range from low to high" specifies clamping between low and high, but the code uses min(x, low) which is incorrect — it should be min(x, high). For example, if x=10, low=5, high=15, the function returns max(5, min(10, 5)) = 5, but it should return 10. The correct clamping should be max(low, min(x, high)).
Fix: return max(low, min(x, high))
