load('api_config.js');
load('api_mqtt.js');
load('api_timer.js');
load('api_dht.js');
load('api_config.js');
load('api_gpio.js');
load('api_mqtt.js');
load('api_net.js');
load('api_sys.js');
load('api_timer.js');
load('api_dht.js');

let deviceName = Cfg.get('device.id');
let topic_pub = '/devices/' + deviceName + '/events';
let isConnected = false;
let dhtPin = Cfg.get('app.dht');
let redPin = Cfg.get('app.red');
let greenPin = Cfg.get('app.green');
let bluePin = Cfg.get('app.blue');
let buttonPin = Cfg.get('app.button');
let dht = DHT.create(dhtPin, DHT.DHT11);
let topic_sub = '/devices/' + Cfg.get('device.id') + '/config';

let demo_mode = false;

GPIO.set_mode(redPin, GPIO.MODE_OUTPUT);
GPIO.set_mode(greenPin, GPIO.MODE_OUTPUT);
GPIO.set_mode(bluePin, GPIO.MODE_OUTPUT);

GPIO.set_button_handler(buttonPin, GPIO.PULL_UP, GPIO.INT_EDGE_NEG, 200, function () {
  demo_mode = !demo_mode;
  print('#### DEMO MODE: ',demo_mode);
}, null);

MQTT.sub(topic_sub, function(conn, top, msg) {
  print('Got config update:', msg.slice(0, 100));
  let obj = JSON.parse(msg);
  if(obj.score<=1){
    GPIO.write(redPin, true);
    GPIO.write(greenPin, false);
    GPIO.write(bluePin, false);
  } else if(obj.score >=2 && obj.score <=3){
    GPIO.write(redPin, true);
    GPIO.write(greenPin, true);
    GPIO.write(bluePin, false);
  } else if(obj.score >=4) {
    GPIO.write(redPin, false);
    GPIO.write(greenPin, true);
    GPIO.write(bluePin, false);
  }
}, null);

let getInfo = function() {
  let temperature; let humidity; let pressure; let dewpoint;
  if (demo_mode){
    temperature = 65;
    humidity = 95;
    pressure = 1028;
    dewpoint = 64;
  } else {
    temperature = dht.getTemp()*9/5+32;
    humidity = dht.getHumidity();
    pressure = 1028;
    dewpoint = temperature = (9/25*(100-humidity));
  }
  return JSON.stringify({
    temperature: temperature,
    humidity: humidity,
    pressure: pressure,
    timecollected: Timer.fmt("%Y-%m-%d %H:%M:%S", Timer.now()),
    sensorID: 5641906755207168,
    dewpoint: dewpoint,
    predict: true
  });
};

Timer.set(
  60 * 1000,
  true,
  function() {
    print('Info:', getInfo());
    if (isConnected) {
      publishData();
    }
  },
  null
);

MQTT.setEventHandler(function(conn, ev) {
  if (ev === MQTT.EV_CONNACK) {
    print('CONNECTED');
    isConnected = true;
    publishData();
  }
}, null);

function publishData() {
  let ok = MQTT.pub(topic_pub, getInfo());
  if (!ok) {
    print('Error publishing');
  }
}

// Monitor network connectivity.
Net.setStatusEventHandler(function(ev, arg) {
  let evs = '???';
  if (ev === Net.STATUS_DISCONNECTED) {
    evs = 'DISCONNECTED';
  } else if (ev === Net.STATUS_CONNECTING) {
    evs = 'CONNECTING';
  } else if (ev === Net.STATUS_CONNECTED) {
    evs = 'CONNECTED';
  } else if (ev === Net.STATUS_GOT_IP) {
    evs = 'GOT_IP';
  }
  print('== Net event:', ev, evs);
}, null);
