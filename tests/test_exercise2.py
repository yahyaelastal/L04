import os
import sqlite3
import subprocess

import pytest

import exercise2
from exercise2 import *


# bug report 1
def test_r1_is_passing_with_grade_5():
    assert is_passing(5) is True


# bug report 2
def test_r2_valid_password_length_8():
    assert is_valid_password("password123") is True


# bug report 3
def test_r3_clamp_bug():
    assert clamp(10, 5, 15) == 10
