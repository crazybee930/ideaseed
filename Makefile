version:
	poetry version $(VERSION) && sed -i -e "s/^VERSION = .*/VERSION = Version(\"$(VERSION)\")/g" ideaseed/constants.py
