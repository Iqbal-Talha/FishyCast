import { useEffect, useState } from "react";
import React from 'react';
import Dropdown from 'react-dropdown';
import io from "socket.io-client";

import "./home.css";
import 'react-dropdown/style.css';

const Home = () => {
  //############################## Variables ##############################
  const options = [
    'Node10', 'Node22'
  ];
  const [node, setNode] = useState('Node10');
  const [todayTemp, setTodayTemp] = useState('');
  const [todayPrecip, setTodayPrecip] = useState('');
  const [yesterdayTemp, setYesterdayTemp] = useState('');
  const [yesterdayPrecip, setYesterdayPrecip] = useState('');
  const [outputTotal, setOutputTotal] = useState('N/A');
  const [outputTime, setOutputTime] = useState('N/A');
  



  //############################## Websocket ##############################
  const socket = io("http://localhost:5000");

  // Handle WebSocket events
  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to server');
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    return () => {
      socket.disconnect();
    };
  }, []);




  //############################## Get predictions ##############################
  const makePredictions = async () => {
    socket.emit('predict', { node, todayTemp, todayPrecip, yesterdayTemp, yesterdayPrecip });
    
    await socket.on('prediction_result', (data) => {
      if(data.total < 0)
      {
        setOutputTotal('No Fish');
        setOutputTime('No Fish');
      }
      else
      {
        setOutputTotal(data.total);
        setOutputTime(data.time);
      }
    });
  };



  //############################## isNumeric ##############################
  const isNumeric = value => !isNaN(parseFloat(value)) && isFinite(value);



  //############################## Get input ##############################
  const getInput = async () => {
    if (!isNumeric(todayTemp) || !isNumeric(todayPrecip) || !isNumeric(yesterdayTemp) || !isNumeric(yesterdayPrecip)) {
      alert('Invalid state values. Please ensure all values are numerical.');
    }
    else{
      await makePredictions();
    }
  }




  //############################## Page ##############################
  return (
    <div className="home">
      <div className="header">
        <b className="h1">FishyCast Salmonoid Forecast</b>
      </div>
      <div className="body">
        <div className="description-section">
          <div className="description">DESCRIPTION</div>
          <div className="this-app-takes">
            This app takes data from Biotactic under water camera that uses AI and computer vision to count Salmonoids
            passing at Thornbury Fishway exit, Beaver River, Ontario and Bowmanville Creek, Bowmanville, Ontario, Canada. 
            Utilizing Logistic regression and Neural Networks it takes into consideration the weather of today and yesterday 
            to predict the expected population of fish in the area, stating the peak amount and time.
          </div>

          <div className="node-info">
            Node10: Thornbury, Node22: Bowmanville
          </div>
        </div>


        <div>
          <Dropdown options={options} value={node} onChange={(event) => setNode(event.target.value)} />
        </div>


        <div className="input-section">
          <div className="description">INPUT</div>
          <div className="input-values">
            <div className="today-values">
              <div className="today-temp">
                <div className="description">Today's Temperature (°C):</div>
                <input className="input-field" id="today-temp" value={todayTemp} onChange={(event) => setTodayTemp(event.target.value)}/>
              </div>
              <div className="today-temp">
                <div className="description">Today's Precipitation (mm):</div>
                <input className="input-field" id="today-precip" type="text" value={todayPrecip} onChange={(event) => setTodayPrecip(event.target.value)}/>
              </div>
            </div>
            <div className="today-values">
              <div className="today-temp">
                <div className="description">Yesterday's Temperature (°C):</div>
                <input className="input-field" id="yesterday-temp" value={yesterdayTemp} onChange={(event) => setYesterdayTemp(event.target.value)}/>
              </div>
              <div className="today-temp">
                <div className="description"> Yesterday's Precipitation (mm):</div>
                <input className="input-field" id="yesterday-precip" value={yesterdayPrecip} onChange={(event) => setYesterdayPrecip(event.target.value)}/>
              </div>
            </div>
          </div>
        </div>


        <div className="input-section">
          <button type="button" className="submit-button" onClick={getInput}>PREDICT</button>
        </div>


        <div className="input-section">
          <div className="description">RESULT</div>
          <div className="result1">
            <div className="today-result">
              <div className="description">Total Fish Today:</div>
              <div className="output-total">{outputTotal}</div>
            </div>
            <div className="today-result">
              <div className="description">Peak Time:</div>
              <div className="output-time">{outputTime}</div>
            </div>
          </div>
        </div>
        <img className="fish-meter-icon" alt="" src="/fishmeter.svg" />
      </div>
    </div>
  );
};

export default Home;
