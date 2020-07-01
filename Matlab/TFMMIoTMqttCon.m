% Create an MQTT connection to hivemq public broker.
global myMQTT topicMov
myMQTT = mqtt(brokerAddress, 'Port', portMqtt);

%Subscribe to a topic
%mySub = subscribe(myMQTT, topic)

%Publish a message to a topic
%publish(myMQTT, topic, 'testMessage');