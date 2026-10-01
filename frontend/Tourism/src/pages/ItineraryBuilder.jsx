import { useState } from 'react'
import { FiPlus, FiTrash2, FiMapPin, FiDollarSign, FiClock, FiShare2, FiDownload } from 'react-icons/fi'

const ItineraryBuilder = () => {
  const [itinerary, setItinerary] = useState({
    title: 'My Nepal Trip',
    startDate: '',
    endDate: '',
    days: [
      { day: 1, stops: [] }
    ]
  })
  const [budget, setBudget] = useState({ accommodation: 0, food: 0, transport: 0, activities: 0 })
  const [showShare, setShowShare] = useState(false)

  const addDay = () => {
    setItinerary({
      ...itinerary,
      days: [...itinerary.days, { day: itinerary.days.length + 1, stops: [] }]
    })
  }

  const removeDay = (dayIndex) => {
    if (itinerary.days.length <= 1) return
    setItinerary({
      ...itinerary,
      days: itinerary.days.filter((_, idx) => idx !== dayIndex)
    })
  }

  const addStop = (dayIndex, id) => {
    const newDays = [...itinerary.days]
    newDays[dayIndex].stops.push({
      id,
      name: '',
      time: '',
      notes: ''
    })
    setItinerary({ ...itinerary, days: newDays })
  }

  const removeStop = (dayIndex, stopIndex) => {
    const newDays = [...itinerary.days]
    newDays[dayIndex].stops = newDays[dayIndex].stops.filter((_, idx) => idx !== stopIndex)
    setItinerary({ ...itinerary, days: newDays })
  }

  const updateStop = (dayIndex, stopIndex, field, value) => {
    const newDays = [...itinerary.days]
    newDays[dayIndex].stops[stopIndex][field] = value
    setItinerary({ ...itinerary, days: newDays })
  }

  const totalBudget = Object.values(budget).reduce((a, b) => a + b, 0)

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Itinerary Builder</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowShare(true)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <FiShare2 className="w-4 h-4" />
            Share
          </button>
          <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center gap-2">
            <FiDownload className="w-4 h-4" />
            Export PDF
          </button>
        </div>
      </div>

      {/* Trip Details */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <input
          type="text"
          value={itinerary.title}
          onChange={(e) => setItinerary({ ...itinerary, title: e.target.value })}
          className="w-full text-xl font-semibold border-none outline-none bg-transparent mb-4"
          placeholder="Trip Title"
        />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
            <input
              type="date"
              value={itinerary.startDate}
              onChange={(e) => setItinerary({ ...itinerary, startDate: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
            <input
              type="date"
              value={itinerary.endDate}
              onChange={(e) => setItinerary({ ...itinerary, endDate: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>
      </div>

      {/* Budget */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FiDollarSign className="w-5 h-5" />
          Budget Calculator
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { key: 'accommodation', label: 'Accommodation' },
            { key: 'food', label: 'Food' },
            { key: 'transport', label: 'Transport' },
            { key: 'activities', label: 'Activities' },
          ].map(item => (
            <div key={item.key}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{item.label}</label>
              <input
                type="number"
                value={budget[item.key]}
                onChange={(e) => setBudget({ ...budget, [item.key]: Number(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                placeholder="0"
              />
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
          <p className="text-lg font-semibold text-emerald-600">
            Total Budget: NPR {totalBudget.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Days */}
      <div className="space-y-4">
        {itinerary.days.map((day, dayIndex) => (
          <div key={dayIndex} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Day {day.day}</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => addStop(dayIndex, Date.now())}
                  className="px-3 py-1 text-emerald-600 hover:bg-emerald-50 rounded-lg text-sm flex items-center gap-1"
                >
                  <FiPlus className="w-4 h-4" />
                  Add Stop
                </button>
                {itinerary.days.length > 1 && (
                  <button
                    onClick={() => removeDay(dayIndex)}
                    className="px-3 py-1 text-red-600 hover:bg-red-50 rounded-lg text-sm"
                  >
                    <FiTrash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {day.stops.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No stops added yet</p>
            ) : (
              <div className="space-y-3">
                {day.stops.map((stop, stopIndex) => (
                  <div key={stop.id} className="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center text-sm font-bold">
                        {stopIndex + 1}
                      </div>
                      {stopIndex < day.stops.length - 1 && (
                        <div className="w-0.5 h-full bg-emerald-200 mt-2" />
                      )}
                    </div>
                    <div className="flex-1 space-y-2">
                      <input
                        type="text"
                        value={stop.name}
                        onChange={(e) => updateStop(dayIndex, stopIndex, 'name', e.target.value)}
                        placeholder="Destination name"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                      />
                      <div className="flex gap-2">
                        <input
                          type="time"
                          value={stop.time}
                          onChange={(e) => updateStop(dayIndex, stopIndex, 'time', e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                        />
                        <input
                          type="text"
                          value={stop.notes}
                          onChange={(e) => updateStop(dayIndex, stopIndex, 'notes', e.target.value)}
                          placeholder="Notes..."
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                        />
                      </div>
                    </div>
                    <button
                      onClick={() => removeStop(dayIndex, stopIndex)}
                      className="text-red-500 hover:bg-red-50 p-2 rounded"
                    >
                      <FiTrash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={addDay}
        className="w-full mt-4 px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-emerald-500 hover:text-emerald-600 flex items-center justify-center gap-2"
      >
        <FiPlus className="w-5 h-5" />
        Add Day
      </button>

      {/* Share Modal */}
      {showShare && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Share Itinerary</h3>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value="https://nepalyatra.com/shared/abc123"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
              />
              <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">
                Copy
              </button>
            </div>
            <button
              onClick={() => setShowShare(false)}
              className="w-full mt-4 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ItineraryBuilder
