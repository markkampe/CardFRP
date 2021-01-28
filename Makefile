BASE_CLASSES = base.py gameobject.py gameactor.py gameaction.py gamecontext.py dice.py
SUB_CLASSES = npc_guard.py
DEMO = scenarios.py
PYTESTS = test_cardfrp.py

ALL = $(BASE_CLASSES) $(SUB_CLASSES) $(DEMO) $(PYTESTS)

demo: $(DEMO)
	python3 $(DEMO)

test:
	for file in $(BASE_CLASSES) $(SUB_CLASSES); do	\
		echo "\n\n=========================";	\
		echo "TESTING $$file";			\
		echo "=========================";	\
		python3 $$file;				\
		done
	echo "\n\n=========================";	\
	echo "RUNNING MULTI-CLASS PyTests";	\
	echo "=========================";	\
	pytest-3 -v

doc:
	epydoc -v --graph=umlclasstree $(BASE_CLASSES) $(SUB_CLASSES)
	@echo PyDocumentation can be found in html subdirectory

DISABLES= --disable=duplicate-code --disable=fixme
lint:
	pylint3 $(DISABLES) $(ALL)
	pep8 $(ALL)

clean:
	-rm -f *.pyc
	-rm -f __pycache__/*
	-rm -rf html

