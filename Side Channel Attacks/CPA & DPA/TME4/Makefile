CC = gcc  # C compiler
CFLAGS = -fPIC -Wall -Wextra -Werror # C flags
LDFLAGS = -shared   # linking flags
RM = rm -f   # rm command
TARGET_LIB = cpa/cpa_attack.so  # target lib

SRCS = cpa/cpa_attack.c  # source files

OBJS = $(SRCS:.c=.o)

.PHONY: all
all: ${TARGET_LIB}

$(TARGET_LIB): $(OBJS)
	$(CC) ${LDFLAGS} -o $@ $^
	@echo "\033[1;32m ==========[ CPA ATTACK LIBRARY SUCCESSFULLY CREATED ]=========="


.PHONY: clean
clean:
	-${RM} ${TARGET_LIB} ${OBJS}
	@echo "\033[1;31m$(TARGET_LIB) ==> DELETED"
	@echo "\033[1;31m$(OBJS) ==> DELETED"
