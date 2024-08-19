/**
 * @author Jayson De La Vega
 * @date 2024-8-24
 * @ C Library for serial communication
 *
 * Adapted from
 * https://stackoverflow.com/questions/6947413/how-to-open-read-and-write-from-serial-port-in-c
 */
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#include <stdio.h>

int main(int argc, char *argv[]) {

  if (argc != 2) {
    printf("Usage: %s <serial port>\n", argv[0]);
    return -1;
  }
  char *portName = argv[1];

  int fd = open(portName, O_RDWR | O_NOCTTY | O_SYNC);
  if (fd < 0) {
    printf("Error %d opening %s: %s\n", errno, portName, strerror(errno));
    return -1;
  } else {
    printf("Opened %s\n", portName);
  }

  set_interface_attribs(fd, B115200, 0);
  enable_blocking(fd, 1);

  const int buff_len = 7;
  char buff[] = {0x0, 0x1, 0x2, 0x3, 0x4, '\n'};
  write(fd, "hello\n", buff_len);
  printf("wrote %d bytes\n", buff_len);

  usleep((7 + 25) * 100);

  char buf[100];
  int n = read(fd, buf, sizeof(buf));

  printf("read %d bytes\n", n);

  return 0;
}
