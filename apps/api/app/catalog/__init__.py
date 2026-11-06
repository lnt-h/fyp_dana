"""Catalog repositories (architecture §2): published places, search, reference data, preferences.

Plain classes and functions over an ``AsyncSession`` with explicit selects (the models declare no
ORM relationships). This package never imports the HTTP layer or any AI code.
"""
