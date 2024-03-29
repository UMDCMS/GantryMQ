/**
 * @file gcoder.cc
 * @author Yi-Mu Chen
 * @brief Implementation of the GCode transfer interface.
 *
 * @class GCoder
 * @ingroup hardware
 * @brief Handling the transmission of gcode motion commands.
 *
 * @details Handling the transmission of gcode commands used for motion control
 * from raw gcode operations to user-ready, human-readable function with
 * appropriate abstraction of command sequences and additional signal parsing
 * between commands. The GCoder class is responsible for the transmission of
 * instructions to the 3D-printer for motion control. The transmission in
 * performed over USB using the UNIX termios interface. The full documentation
 * could be found [here][s-port].
 *
 * The class also abstracts motion controls which may or may not involve many
 * gcode commands into single functions with parameters which is simpler to call
 * for end users. For the full list of available marlin-flavored gcode, see
 * [here][marlin]. Due to how communications is handled in the kernel, not all
 * motions is abstracted in C++, with some needing to be handled at python
 * level. Those will be high-lighted for in the various code segments.
 *
 * [s-port]: https://www.xanthium.in/Serial-Port-Programming-on-Linux
 * [marlin]: https://marlinfw.org/meta/gcode/
 */
#include "sysfs.hpp"
#include "threadsleep.hpp"

// Standard C++ libraries
#include <cmath>
#include <fmt/core.h>
#include <string>

// Stuff required for tty input and output
#include <sys/file.h>
#include <termios.h>

// Pybind11
#include <pybind11/pybind11.h>

class GCoder : private hw::fd_accessor
{
public:
  // Constructor and destructor
  GCoder( const std::string& dev_path );
  GCoder()                 = delete;
  GCoder( const GCoder& )  = delete;
  GCoder( const GCoder&& ) = delete;
  ~GCoder();

  static float        _max_x;
  static float        _max_y;
  static float        _max_z;
  inline static float GetMaxX() { return _max_x; }
  inline static float GetMaxY() { return _max_y; }
  inline static float GetMaxZ() { return _max_z; }
  inline static void  SetMaxX( const float val ) { _max_x = val; }
  inline static void  SetMaxY( const float val ) { _max_y = val; }
  inline static void  SetMaxZ( const float val ) { _max_z = val; }

  std::string RunGcode( const std::string& gcode, const unsigned waitack = 1e4, const unsigned attempt = 0 ) const;

  // Motion command abstraction
  std::string GetSettings() const;
  void        SendHome( bool x, bool y, bool z );
  void        EnableStepper( bool x, bool y, bool z );
  void        DisableStepper( bool x, bool y, bool z );
  void        SetSpeedLimit( float x = std::nanf( "" ), float y = std::nanf( "" ), float z = std::nanf( "" ) );

  void clear_buffer() const;

  //
  void MoveTo( float x = std::nanf( "" ), float y = std::nanf( "" ), float z = std::nanf( "" ) );
  bool UpdateCoordinate();
  bool InMotion();

  // Floating point comparison.
  static bool MatchCoord( float x, float y );
  float       ModifyTargetCoordinate( float orig, const float max );

  static inline float round_val( float x ) { return std::round( x * 10 ) / 10; }

  // Operation variables
  float opx, opy, opz; /** target position of the printer */
  float cx, cy, cz;    /** current position of the printer */
  float vx, vy, vz;    /** Speed of the gantry head. */
};

/**
 * @brief Hard limit coordinates for gantry motion.
 * @details As there are now stop limiter for the gantry maximum motion range
 * value, here, programmatically add a hard input into the system to avoid
 * hardware damaged.
 * @{
 */
float GCoder::_max_x = 345;
float GCoder::_max_y = 200;
float GCoder::_max_z = 460;

/** @} */

/**
 * @brief Forward declaration of static helper functions.
 */
static bool
check_ack( const std::string& cmd, const std::string& msg );

/**
 * @brief Initializing the communications interface.
 *
 * Low level instructions in the termios interface for setting up the read
 * speed and mode for the communicating with the printer over USB. This part of
 * the code currently considered black-magic, as most of the statements are
 * copy from [here][s-port], so do not edit statements containing the tty
 * container unless you are absolutely sure about what you are doing.
 *
 * After initialization, the printer will always perform these 3 steps:
 * - Send the gantry back home and reset coordinates ot (0,0,0).
 * - Set the motion speed to something much faster
 * - Set the acceleration speed to 3 times the factory default.
 *
 * [s-port]: https://www.xanthium.in/Serial-Port-Programming-on-Linux
 */
GCoder::GCoder( const std::string& dev_path )
  : //
  hw::fd_accessor( "GCoder", dev_path, O_RDWR | O_NOCTTY | O_NONBLOCK | O_ASYNC )
{
  static const int speed = B115200;

  struct termios tty;

  if( tcgetattr( this->_fd, &tty ) < 0 ) {
    raise_error( fmt::format( "Error getting termios settings. Returned code [{0:s}]", strerror( errno ) ) );
  }

  cfsetospeed( &tty, (speed_t)speed );
  cfsetispeed( &tty, (speed_t)speed );

  tty.c_cflag |= ( CLOCAL | CREAD ); // ignore modem controls
  tty.c_cflag &= ~CSIZE;
  tty.c_cflag |= CS8;      // 8-bit characters
  tty.c_cflag &= ~PARENB;  // no parity bit
  tty.c_cflag &= ~CSTOPB;  // only need 1 stop bit
  tty.c_cflag &= ~CRTSCTS; // no hardware flowcontrol

  // setup for non-canonical mode
  tty.c_iflag &= ~( IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON );
  tty.c_lflag &= ~( ECHO | ECHONL | ICANON | ISIG | IEXTEN );
  tty.c_oflag &= ~OPOST;

  // fetch bytes as they become available
  tty.c_cc[VMIN]  = 0;
  tty.c_cc[VTIME] = 0;

  if( tcsetattr( this->_fd, TCSANOW, &tty ) != 0 ) {
    raise_error( fmt::format( "Error setting termios. Returned code [{0:s}]", strerror( errno ) ) );
  }

  printmsg( "Waking up printer...." );
  hw::sleep_seconds( 10 );
  clear_buffer(); // Flushing the buffer is required for first start up ()
  SendHome( true, true, true );
  hw::sleep_milliseconds( 5 );

  // Setting speed to be as fast as possible
  SetSpeedLimit( 1000, 1000, 1000 );

  // Setting acceleration to 3x the factory default:
  RunGcode( "M201 X1000 Y1000 Z300", 1e5 );

  return;
}

/**
 * @brief Main function abstraction for sending a gcode command to the session.
 *
 * As a standard in this program, all gcode command string should end in a
 * newline character. This function will parse the gcode string to the printer
 * via the defined interface, and pass the return string of the printer as the
 * return value. Notice that the function will check the return string for the
 * acknowledgement string ("ok" at the start of a line) to know that the
 * command has been executed by the printer. If this acknowledgement string is
 * not received after a wait period, then the command is tried again up to 10
 * times.
 *
 * Notice that exactly when the acknowledgement string is reported will depend
 * on the gcode command in question, and so later functions of abstracting
 * gcode commands should be responsible for choosing an appropriate timeout
 * duration to reduce multiple function calls.
 */
std::string
GCoder::RunGcode( const std::string& gcode, const unsigned wait_ack, const unsigned attempt ) const
{
  using namespace std::chrono;

  // static variables
  static const unsigned maxtry = 10;

  if( attempt >= maxtry ) {
    raise_error( fmt::format(
      R"(ACK string for command [{0:s}] was not received after [{1:d}]
      attempts! The message could be dropped or there is something wrong with
      the device!)",
      gcode,
      maxtry ) );
  }

  // Sending output
  printdebug( fmt::format( "[{0:s}] to USBTERM[{1:s}] (attempt {2:d})", gcode, this->_dev_path, attempt ) );
  this->write( gcode + "\n" ); // Adding an end of string character
  tcdrain( this->_fd );

  high_resolution_clock::time_point start = high_resolution_clock::now();

  for( high_resolution_clock::time_point now = high_resolution_clock::now();
       duration_cast<microseconds>( now - start ).count() < wait_ack;
       now = high_resolution_clock::now() ) {
    hw::sleep_milliseconds( 1 );
    const std::string ack_string = this->read_str();

    if( check_ack( gcode, ack_string ) ) {
      printdebug( fmt::format( "Request [{0:s}] is done!", gcode ) );
      clear_buffer();
      return ack_string;
    }
  }
  return RunGcode( gcode, wait_ack, attempt + 1 );
}

void
GCoder::clear_buffer() const
{
  // Flushing buffer by repeated read actions
  for( unsigned n = 1; n > 0; n = this->read_str().length() ) {
    hw::sleep_milliseconds( 5 );
  }
}

/**
 * @brief Private function for checking the acknowledgement string for gcode
 * execution completion.
 *
 * A typically return string after issuing a command will be the:
 * "<return_string>\nok\n", this will be the message that we are looking for.
 * But, the printer will periodically flush the printer settings via the
 * automatic M503 calls that would have the printer accidentally assume the
 * command has been completed when it has not.
 *
 * This function looks at the return message string, and filters on the more
 * obscure commands in our use case, and only returns true if the return message
 * is not a settings report.
 */
static bool
check_ack( const std::string& cmd, const std::string& msg )
{
  if( msg.length() == 0 ) {
    return false;
  }
  auto has_substr = []( const std::string& str, const std::string& sub ) -> bool {
    return str.find( sub ) != std::string::npos;
  };
  if( !has_substr( msg, "ok" ) ) {
    return false;
  }
  if( has_substr( msg, "M200" ) ) {
    if( !has_substr( cmd, "M503" ) && !has_substr( cmd, "M200" ) ) {
      return false;
    }
  }
  return true;
}

/**
 * @brief Sending the gantry to home.
 *
 * The gcode command G28 can have each of the axis sent reset for the axis. This
 * also wipes the current stored axis coordinates to 0
 */
void
GCoder::SendHome( bool x, bool y, bool z )
{
  std::string gcode = "G28";

  if( !x && !y && !z ) {
    return;
  }

  if( x ) {
    gcode += " X";
    opx = 0;
    cx  = 0;
  }

  if( y ) {
    gcode += " Y";
    opy = 0;
    cy  = 0;
  }

  if( z ) {
    gcode += " Z";
    opz = 0;
    cz  = 0;
  }

  RunGcode( gcode, 4e9 );
}

/**
 * @brief Disabling the stepper motors.
 *
 * The power supply of the gantry is rather noisy, causing issues with the
 * readout system. Disabling the stepper closes the relevant power supplies
 * while the gantry still remembers where it is, at the cost of less stability
 * of the gantry position. Python will be handling for disabling the stepper
 * motors when readout systems are invoked.
 */
void
GCoder::DisableStepper( bool x, bool y, bool z )
{
  if( x ) {
    RunGcode( "M18 X E", 1e5 );
  }
  if( y ) {
    RunGcode( "M18 Y E", 1e5 );
  }
  if( z ) {
    RunGcode( "M18 Z E", 1e5 );
  }
}

/**
 * @brief Enabling the stepper motors.
 *
 * This should be used after the readout has been completed to reduce the
 * changes of gantry position drifting.
 */
void
GCoder::EnableStepper( bool x, bool y, bool z )
{
  if( x ) {
    RunGcode( "M17 X", 1e5 );
  }
  if( y ) {
    RunGcode( "M17 Y", 1e5 );
  }
  if( z ) {
    RunGcode( "M17 Z", 1e5 );
  }
}

/**
 * @brief Getting a list of settings a the string reported by the gantry.
 */
std::string
GCoder::GetSettings() const
{
  return RunGcode( "M503" );
}

/**
 * @brief Setting the motion speed limit (in units of mm/s)
 *
 * There are two steps to setting the motion speeds:
 * 1. Setting the maximum feed rate (M203)
 * 2. Set the feed rate of all future G0 commands (G0 F), this is units of
 *    mm/minutes!
 *
 * In addition we will be setting some hard maximum limits on the motion speed
 * rate:
 * - For x/y: 200mm/s
 * - For z: 30mm/s
 *
 * While setting values to higher is programmatically possible, empirically this
 * is found to make the gantry motion unstable.
 */
void
GCoder::SetSpeedLimit( float x, float y, float z )
{
  static const float maxv = 200.0; // Setting the maximum speed
  static const float maxz = 30.0;  // Maximum speed for z axis

  // NAN detection.
  if( x != x ) {
    x = vx;
  }
  if( y != y ) {
    y = vy;
  }
  if( z != z ) {
    z = vz;
  }

  if( x > maxv ) {
    x = maxv;
  }
  if( y > maxv ) {
    y = maxv;
  }
  if( z > maxv ) {
    z = maxz;
  }

  RunGcode( fmt::format( "M203 X{0:.2f} Y{1:.2f} Z{2:.2f}", x, y, z ), 1e5 );

  const float vmax = std::max( std::max( x, y ), z );
  RunGcode( fmt::format( "G0 F{0:.2f}", vmax * 60 ), 1e5 );

  vx = x;
  vy = y;
  vz = z;
}

/**
 * @brief Sending the command for linear motion.
 *
 * This is a very simple interface for the linear motion G0 command, here we
 * will do very minimal parsing on the coordinates:
 *
 * - Make sure that the (x,y,z) coordinates are within physical limitations.
 * - Round the coordinates to the closest 0.1 mm value.
 *
 * Notice that the G0 command will return the ACK string immediate after
 * receiving the command, not after the motion is completed for this reason,
 * additional parsing is required for make sure the motion has completed.
 */
void
GCoder::MoveTo( float x, float y, float z )
{
  // Setting up target position
  opx = ( x == x ) ? x : opx;
  opy = ( y == y ) ? y : opy;
  opz = ( z == z ) ? z : opz;

  // Rounding to closest 0.1 (precision of gantry system)
  opx = ModifyTargetCoordinate( opx, GCoder::_max_x );
  opy = ModifyTargetCoordinate( opy, GCoder::_max_y );
  opz = ModifyTargetCoordinate( opz, GCoder::_max_z );

  // Running the code
  RunGcode( fmt::format( "G0 X{0:.1f} Y{1:.1f} Z{2:.1f}", opx, opy, opz ), 1000 );

  return;
}

/**
 * @brief Extracting the current coordinates using the M114 gcode command
 *
 * Returns whether the string parsing is completed
 */
bool
GCoder::UpdateCoordinate()
{
  float a, b, c, temp; // feed position of extruder.
  float x, y, z;       // Temporary storage of the extract coordinates.
  try {
    const int check =
      sscanf( RunGcode( "M114" ).c_str(), "X:%f Y:%f Z:%f E:%f Count X:%f Y:%f Z:%f", &a, &b, &c, &temp, &x, &y, &z );
    if( check != 7 ) {
      return false;
    } // Early exit for bad parse
    else {
      cx = x;
      cy = y;
      cz = z;
      return true;
    }
  } catch( std::exception& e ) { // Return false if command fails
    return false;
  }
}

/**
 * @brief Checking whether the gantry has completed the motion to a set of
 * coordinates.
 *
 * The file description interface used for communicating with the gantry does
 * not play well with other interfaces when used as a continuous stream. So
 * rather than having the file interface suspend the thread while the gantry is
 * in motion, we opt to have the gantry perform simple one-off checks, and have
 * thread suspension be handled by the higher interfaces.
 */
bool
GCoder::InMotion()
{
  if( UpdateCoordinate() ) {
    return !( MatchCoord( opx, cx )    //
              && MatchCoord( opy, cy ) //
              && MatchCoord( opz, cz ) );
  } else { // If updating coordinates failed. Assume the gantry is in motion
    return true;
  }
}

/**
 * @brief Simple function to check if two coordinate values are identical, within
 * the gantry resolution of 0.1 mm
 */
bool
GCoder::MatchCoord( const float x, const float y )
{
  // Rounding to closes 0.1
  return GCoder::round_val( x ) == GCoder::round_val( y );
}

/**
 * @brief Modifying the original target coordinate to somewhere that can be
 * accessed by the gantry
 *
 * Original given some original coordinate value, we return a modified target
 * coordinate such that:
 * - the return value is always larger than the minimum value 0.1
 * - The return value is always smaller than the given maximum value.
 * - The return value is rounded to the closest 0.1 decimal place.
 *
 * This ensure that given any input coordinate. the target coordinate will
 * always be some value that the physically safe target for the gantry. If the
 * target value is modified in any way other than simple rounding, then an
 * error message will be displayed to ensure notify the user of these
 * modifications.
 */
float
GCoder::ModifyTargetCoordinate( const float original, const float max_value )
{
  float ans = GCoder::round_val( original ); // rounding to closest
  if( ans < 0.1 ) {
    printwarn( fmt::format(
      R"(Target coordinate values [{0:.1f}] is below the lower limit 0.1.
                 Modifying the target motion coordinate to 0.1 to avoid damaging
                 the system)",
      ans ) );
    return 0.1;
  } else if( ans > max_value ) {
    printwarn( fmt::format(
      R"(Target coordinate values [{0:.1f}] is above upper limit
                 [{1:.1f}]. Modifying the target motion coordinate to [{1:.1f}] to
                 avoid damaging the system)",
      ans,
      max_value ) );

    return GCoder::round_val( max_value );
  } else {
    return ans;
  }
}

/**
 * @brief Destructing the GCoder::GCoder object
 *
 * Attempt to move close to the home position before deallocating (faster start
 * up for the next startup instance).
 */
GCoder::~GCoder()
{
  try {
    this->MoveTo( 1, 1, 1 ); // 1 mm away from home
  } catch( std::exception& err ) {
    // Do nothing if something errors out.
  }
  printdebug( "Deallocating the gantry controls" );
}

PYBIND11_MODULE( gcoder, m )
{
  pybind11::class_<GCoder>( m, "gcoder" )
    .def( pybind11::init<const std::string&>() )

    // Operation-like functions
    .def( "run_gcode", &GCoder::RunGcode )
    .def( "set_speed_limit", &GCoder::SetSpeedLimit, pybind11::arg( "x" ), pybind11::arg( "y" ), pybind11::arg( "z" ) )
    .def( "move_to", &GCoder::MoveTo, pybind11::arg( "x" ), pybind11::arg( "y" ), pybind11::arg( "z" ) )
    .def( "enable_stepper", &GCoder::EnableStepper, pybind11::arg( "x" ), pybind11::arg( "y" ), pybind11::arg( "z" ) )
    .def( "disable_stepper", &GCoder::DisableStepper, pybind11::arg( "x" ), pybind11::arg( "y" ), pybind11::arg( "z" ) )
    .def( "send_home", &GCoder::SendHome, pybind11::arg( "x" ), pybind11::arg( "y" ), pybind11::arg( "z" ) )

    // Read-like functions
    .def( "get_settings", &GCoder::GetSettings )
    .def( "in_motion", &GCoder::InMotion )

    // Read-like data members (Should only be set via operation-functions)
    .def_readonly( "opx", &GCoder::opx )
    .def_readonly( "opy", &GCoder::opy )
    .def_readonly( "opz", &GCoder::opz )
    .def_readonly( "cx", &GCoder::cx )
    .def_readonly( "cy", &GCoder::cy )
    .def_readonly( "cz", &GCoder::cz )
    .def_readonly( "vx", &GCoder::vx )
    .def_readonly( "vy", &GCoder::vy )
    .def_readonly( "vz", &GCoder::vz )

    // Static methods -- Explicit get/set pair
    .def_static( "get_max_x", &GCoder::GetMaxX )
    .def_static( "get_max_y", &GCoder::GetMaxY )
    .def_static( "get_max_z", &GCoder::GetMaxZ )
    .def_static( "set_max_x", &GCoder::SetMaxX )
    .def_static( "set_max_y", &GCoder::SetMaxY )
    .def_static( "set_max_z", &GCoder::SetMaxZ );
}
