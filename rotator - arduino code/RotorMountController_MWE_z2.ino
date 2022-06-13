/*File Name:  RotorMountController_MWE.ino (V.1.0)
Author:       Daniel Nilsson PhD, Department of Physics, Umea University, Sweden (2021-01-22)
Description:  This Minimal Working Example shows how to control a Rotor Mount (NEMA17 stepper motor) by using a TMC2130 stepper motor driver
              (SilentStepStick) and a ATmega328P based microcontroller incorporating a UART to USB serial bridge (ex. Arduino Uno, Arduino Nano).
              It establishes a command based interface for controlling the Rotor Mount with a Baud rate of 57600 and the EoL characters "Cr+Lf".
Compilation:  Make sure that the following libraries (see "#include <library_name.h>") are downloaded and installed, then select the correct
              board before compiling and the correct port before uploading.
Usage Info:   The serial interface allows programs like Labview to control the Rotor Mount, but for test purposes a Serial Monitor like the one
              included in Arduino's IDE or ones like "Realterm" can be used. (There is limited validation on input data, use with caution!) */
#include <math.h>
#include <Arduino.h>
#include <SerialCommands.h>  // Tested with library V.1.1.0


#include <AccelStepper.h>  // Tested with library V.1.59.0

#include "DRV8825.h"
#define MODE0 10
#define MODE1 11
#define MODE2 12



// Define stepper motor connections and motor interface type. Motor interface type must be set to 1 when using a driver:
#define dirPin 8
#define stepPin 9
#define motorInterfaceType 1
#define SLEEP 13 // optional (just delete SLEEP from everywhere if not used)





// === Stepper Settings ===
#define NR_MICROSTEPS 32  // Driver step size [Microsteps/full step]
#define SM_RESOLUTION 200  // Stepper Motor resolution [Steps/rev] (typically 200)
#define GEAR_RATIO 2  // Mechanical drive wheel and belt reduction [X:1] (Reflective: 1, Transmissive: 2)
//#define STEPPER_CURRENT 700  // Stepper strength [mA]
#define STEPPER_SPEED 4000  // Stepper speed [Microsteps per second] (4k max for ATmega328 @16MHz)
#define STEPPER_ACC 40000  // Stepper Acceleration [Microsteps per second^2]






// === Declaration and Initialization ===
char serial_command_buffer_[32];
void help(SerialCommands* sender);  // Print available commands
void set_rotor_angle(SerialCommands* sender);  // Function to set the angle for the rotor mount
void get_rotor_angle(SerialCommands* sender);  // Function to get the angle from the rotor mount
void set_stepper_speed(SerialCommands* sender);  // Function to set the speed
void stop_stepper(SerialCommands* sender);  // Function to stop
void set_zero(SerialCommands* sender);  // Function to set zero




SerialCommands serial_commands_(&Serial, serial_command_buffer_, sizeof(serial_command_buffer_), "\r\n", " ");
SerialCommand help_("HELP", help);                             // Define "HELP" as the serial command
SerialCommand set_rotor_angle_("SRA", set_rotor_angle);       // Define "SRA" as the serial command
SerialCommand get_rotor_angle_("GRA", get_rotor_angle);       // Define "GRA" as the serial comand
SerialCommand set_stepper_speed_("SSS", set_stepper_speed);   // Define "SSS" as the serial comand
SerialCommand stop_stepper_("STOP", stop_stepper);            // Define "STOP" as the serial comand
SerialCommand set_zero_("ZERO", set_zero);                    // Define "ZERO" as the serial command


DRV8825 driver(SM_RESOLUTION, dirPin, stepPin, SLEEP, MODE0, MODE1, MODE2);
AccelStepper stepper = AccelStepper(motorInterfaceType, stepPin, dirPin);


void setup() {  // Setup routine (Runs once)
  Serial.begin(57600);
  
  
  serial_commands_.SetDefaultHandler(cmd_unrecognized);
  serial_commands_.AddCommand(&help_);
  serial_commands_.AddCommand(&set_rotor_angle_);
  serial_commands_.AddCommand(&get_rotor_angle_);
  serial_commands_.AddCommand(&set_stepper_speed_);
  serial_commands_.AddCommand(&stop_stepper_);
  serial_commands_.AddCommand(&set_zero_);

  
  
  //  driver enable
  //  driver disable
  
  //  set current position(0)


  
  
  driver.begin();  // Initiate pins and registeries (kell RPM érték????)
  driver.enable();
  driver.setMicrostep(NR_MICROSTEPS);  // Set step size
  
  
  stepper.setMaxSpeed(STEPPER_SPEED);  // Set stepper speed
  stepper.setAcceleration(STEPPER_ACC);  // Set stepper acceleration
  Serial.println(F("ROTOR MOUNT CONTROLLER: READY!"));  // Setup done, print to serial
}




void loop() {  // Main loop (Runs forever)
  serial_commands_.ReadSerial();
  stepper.run();
}




void cmd_unrecognized(SerialCommands* sender, const char* cmd) {  // Default handler 
  sender->GetSerial()->print(F("Unrecognized command: ''"));
  sender->GetSerial()->print(cmd);
  sender->GetSerial()->println(F("'', try ''HELP''!"));
}




void help(SerialCommands* sender) {  // Display help
  sender->GetSerial()->println(F("Commands available:"));
  sender->GetSerial()->println(F("Set Rotor Angle: ''SRA <DEGREES>''"));
  sender->GetSerial()->println(F("Get Rotor Angle: ''GRA'' -> DEGREES"));
  sender->GetSerial()->println(F("Set Stepper Speed: ''SSS'' -> microsteps/sec"));
  sender->GetSerial()->println(F("Stop Stepper Motor: ''STOP''"));
  sender->GetSerial()->println(F("Set current position to 0: ''ZERO''"));
}




void set_rotor_angle(SerialCommands* sender) {  // Set the angle [deg] for the rotor mount
  char* arg_str = sender->Next();  //Note: Every call to Next moves the pointer to next parameter
  if (arg_str == NULL) {
    sender->GetSerial()->println(F("ERROR! ROTOR_ANGLE NOT SPECIFIED")); return;
  }
  double rotorAngle = atof(arg_str);  // Convert string to double
  stepper.moveTo((long)SM_RESOLUTION*GEAR_RATIO*NR_MICROSTEPS*rotorAngle/360);  // Calc the #steps and set as target
}




void get_rotor_angle(SerialCommands* sender) {  // Get the angle [deg] from the rotor mount
  sender->GetSerial()->println(360.0*stepper.currentPosition()/((double)SM_RESOLUTION*GEAR_RATIO*(double)NR_MICROSTEPS));  // Calc from #steps
}



void set_stepper_speed(SerialCommands* sender) {  // Set the speed [microsteps/s] for the stepper motor
  char* arg_str = sender->Next();  //Note: Every call to Next moves the pointer to next parameter
  if (arg_str == NULL) {
    sender->GetSerial()->println(F("ERROR! SPEED NOT SPECIFIED")); return;
  }
  float stepperSpeed = atof(arg_str);  // Convert string to integer
  stepper.setMaxSpeed(stepperSpeed);  // Set stepper speed
}



void stop_stepper(SerialCommands* sender) {  // Stop the stepper motor
  stepper.stop();  // Stop stepper motor
}


void set_zero(SerialCommands* sender) {  // set current position to 0
  stepper.setCurrentPosition (0);  // set 0
}
