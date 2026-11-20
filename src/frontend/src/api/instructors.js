import client from './client.js'

export const listInstructors = () => client.get('/instructors').then(r => r.data)
export const getInstructor = (id) => client.get(`/instructors/${id}`).then(r => r.data)
export const createInstructor = (data) => client.post('/instructors', data).then(r => r.data)
export const getInstructorAvailability = (id) => client.get(`/instructors/${id}/availability`).then(r => r.data)
