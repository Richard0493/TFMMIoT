function TFMMIoTSigSave(u)

    global myMQTT topicMov movCode cont 
    global x y z
    
    %x = [x, u(1)];
    %y = [y, u(2)];
    %z = [z, u(3)];
     
    msg = strcat(num2str(posixtime(datetime('now')) * 1e6), " ", num2str(movCode));
    
    for i = 1:size(u, 1)
        msg = strcat(msg, " ", num2str(u(i)));

    end
    
    publish(myMQTT, topicMov, msg);
    cont = cont + 1;

end
