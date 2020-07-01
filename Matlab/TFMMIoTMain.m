
%%
% Conexión MQTT
clc
%clear all
global myMQTT topicMov rawDataMov compMatrix movCodeTrain movCode messValue
global signalPattern01 signalPattern02 signalPattern03
global cont
global wayPoints wayPointsSec01     wayPointsSec02 wayPointsSec03
global q robot fext

brokerAddress = 'tcp://cripta.fdi.ucm.es';
%brokerAddress = 'tcp://192.168.1.52';
portMqtt = 6363;

topicMov = 'dobot/movimiento';

TFMMIoTMqttCon();

%%
% Inicialización de variables
numPoints = 7;

movCode = 1;
movCodeTrain = 1;
wayPointsSec01 = [0 0 0 1 1 1 0; 
                  0 0.5 0.5 0.5 0.5 0 0; 
                  0 0 0 0 0 0 0; 
                  0 1 0.25 0.25 1 0 0; 
                  0 0 0 0 0 1.75 0; 
                  0 1.5 1.25 1.25 1.5 0 0; 
                  0 0 3 4 3 0 0];
              
wayPointsSec02 = [0 0 0 0 0 0 0; 
                  0 0.75 0.75 0.75 0 0 0; 
                  0 0 0 0 0 0 0; 
                  0 -0.3 0 -0.3 0 0 0;  
                  0 0 0 0 0 0 0;
                  0 1.25 0.5 1.5 0 0 0
                  0 0 0 0 0 0 0];
              
wayPointsSec03 = [0 0 0 0.9 0.5 0.9 0; 
                  0 0.6 0.6 0.6 0.6 0 0; 
                  0 0 0 0 0 0 0; 
                  0 -0.5 0 -0.5 0 -0.5 0;  
                  0 0 0 0 0 0 0;
                  0 -0.2 0.7 1 2 0 0
                  0 0 0 0 0 0 0];

wayPoints = wayPointsSec01;

messValue = 0.5;
velPoints = ones(7, numPoints) .* messValue;
accPoints = zeros(7, numPoints);
robot = loadrobot("abbIrb120T","DataFormat","column","Gravity",[0 0 -9.81]);
q = homeConfiguration(robot);
wrench = [0 0 0 0 0 0];
fext = externalForce(robot,'tool0',wrench,q);
