"""
	Utility class for various methods
"""

def chunks(l, n):
	"""
		Split a list into specified chunks
	"""
	n = max(1, n)
	return [l[i:i + n] for i in range(0, len(l), n)]