void setup(){
    Serial.begin(115200);
}
void loop(){
    analogRead(A0);
    analogRead(A1);
    int val1=analogRead(A0);
    int val2=analogRead(A1);
    Serial.print(val1);
    Serial.print(",");
    Serial.println(val2);
}