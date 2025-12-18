import axios from 'axios'

const request = axios.create({
  baseURL: 'http://18.170.57.90/:8000', 
  timeout: 10000
})

export default request
