#define BUFF_LEN 50

typedef struct {
    char rxBuff[BUFF_LEN];
    char txBuff[BUFF_LEN];
    int comm_result;
} packetHandler_t;

void unpack();
  // at first wait for a minimum of 7 characters

  // assume comms failed

  // get number of bytes read
  // find index of packet header
  //    if found at beginning
  //      recalculate length, update waiting length
  //      if received length is less than 
  //    else
  //      remove all preceding bits

void pack();

void updateCRC();

void addPacketStuffing();

void removePacketStuffing();

