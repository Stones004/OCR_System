import { useEffect, useState } from "react"

import Header from "./components/Header/Header"
import Sidebar from "./components/Sidebar/Sidebar"
import Viewer from "./components/Viewer/Viewer"
import Footer from "./components/Footer/Footer"
import SettingsDrawer
  from "./components/SettingsDrawer/SettingsDrawer"

import "./App.css"

import {
  Group,
  Panel,
  Separator
} from "react-resizable-panels"


function App() {

  const [serviceHealth, setServiceHealth] =
    useState({

      api: {
        status: "offline"
      },

      redis: {
        status: "offline"
      },

      gpu_worker: {
        status: "offline"
      },

      telemetry: {
        status: "offline"
      }
    })

  const [theme, setTheme] =
    useState(

      localStorage.getItem(
        "theme"
      ) || "light"
    )

  const connectWebSocket = () => {

    const wsProto =
      window.location.protocol === "https:"
        ? "wss:"
        : "ws:"

    const wsHost =
      window.location.port === "5173"
        ? `${window.location.hostname}:8000`
        : window.location.host

    const ws =
      new WebSocket(
        `${wsProto}//${wsHost}/ws`
      )

    ws.onopen = () => {

      console.log(
        "WEBSOCKET CONNECTED"
      )

      setConnectionStatus(
        "connected"
      )
    }

    ws.onerror = () => {

      setConnectionStatus(
        "disconnected"
      )
    }

    ws.onclose = () => {

      setConnectionStatus(
        "disconnected"
      )
    }

    ws.onmessage = (event) => {

      const data = JSON.parse(
        event.data
      )

      setEvents((prev) => [

        data,

        ...prev
      ])

      // =====================================
      // PAGE EVENTS
      // =====================================

      if (data.event_type === "page_processed") {

        setBooklets(prev => {

          const updated = { ...prev }

          const bookletId =
            data.booklet_id ??
            data.payload?.booklet_id ??
            data.job_id

          const existingBooklet =
            Object.values(updated).find(

              b =>

                b.jobId === data.job_id ||

                b.id === bookletId

            )

          const actualBookletId =
            existingBooklet?.id ??
            bookletId

          if (!actualBookletId) {
            return updated
          }

          if (!updated[actualBookletId]) {

            updated[actualBookletId] = createBooklet({

              bookletId: actualBookletId,

              jobId: data.job_id,

              status: data.status,

              reviewRequired: data.review_required,

              reasons: data.reasons || [],

              imageRoot: actualBookletId

            })

          }

          updated[actualBookletId] = {

            ...updated[actualBookletId],

            jobId: data.job_id,

            status:
              data.status ??
              updated[actualBookletId].status,

            review_required:
              data.review_required ??
              updated[actualBookletId].review_required,

            reasons:
              data.reasons ??
              updated[actualBookletId].reasons

          }

          const existingIndex =
            updated[actualBookletId].pages.findIndex(

              p => p.page_number === data.page_number

            )

          const pageObject = {

            page_number: data.page_number,

            image_path: data.image_path,

            image_width: data.image_width,

            image_height: data.image_height,

            payload:
              data.payload ?? {

                prediction_result:
                  data.prediction_result,

                omr_result:
                  data.omr_result,

                validation_result:
                  data.validation_result

              }

          }

          if (existingIndex >= 0) {

            updated[actualBookletId].pages[existingIndex] =
              pageObject

          }
          else {

            updated[actualBookletId].pages.push(
              pageObject
            )

          }

          updated[actualBookletId].pages.sort(

            (a, b) =>
              a.page_number - b.page_number

          )

          updated[actualBookletId].jobId =
            data.job_id

          if (selectedBooklet?.id === actualBookletId) {

            setSelectedBooklet(
              updated[actualBookletId]
            )

          }

          return updated
        }
        )
      }



      // =====================================
      // JOB COMPLETED EVENTS
      // =====================================

      if (data.event_type === "job_completed") {

        console.log("JOB COMPLETED EVENT", data)

        setBooklets(prev => {

          const updated = { ...prev }

          const bookletId =
            data.booklet_id ??
            data.job_id

          const existingBooklet =

            Object.values(updated).find(

              b =>

                b.jobId === data.job_id ||

                b.id === bookletId

            )

          const actualBookletId =

            existingBooklet?.id ??

            bookletId

          if (!updated[actualBookletId]) {

            updated[actualBookletId] = createBooklet({

              bookletId: actualBookletId,

              jobId: data.job_id,

              status: data.status,

              reviewRequired: data.review_required,

              reasons: data.reasons || [],

              imageRoot: actualBookletId

            })

          }

          updated[actualBookletId] = {

            ...updated[bookletId],

            jobId: data.job_id,

            status: data.status,

            review_required: data.review_required,

            reasons: data.reasons || []

          }

          if (selectedBooklet?.id === bookletId) {

            setSelectedBooklet(updated[bookletId])

            if (selectedPage) {

              const page = updated[bookletId].pages.find(
                p => p.page_number === selectedPage.page_number
              )

              if (page) {
                setSelectedPage(page)
              }
            }
          }

          return updated

        })
      }

    }   // closes ws.onmessage

    return ws

  }     // 

  const [events, setEvents] = useState([])

  const [booklets, setBooklets] = useState({})

  const [selectedPage, setSelectedPage] = useState(null)

  const [selectedBooklet, setSelectedBooklet] = useState(null)

  const [settingsOpen, setSettingsOpen] = useState(false)

  const [connectionStatus, setConnectionStatus] = useState("connecting")

  const updateBookletStatus = async (

    jobId,

    bookletId,

    newStatus

  ) => {

    try {

      // TODO:
      // Replace with actual API

      await fetch(

        `/jobs/${jobId}/status`,

        {

          method: "PATCH",

          headers: {

            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({

            status: newStatus
          })
        }
      )

      setBooklets(prev => {

        const updated = {
          ...prev
        }

        if (

          updated[bookletId]

        ) {

          updated[bookletId] = {

            ...updated[bookletId],

            status: newStatus
          }

          console.log(
            "STATUS UPDATED",
            bookletId,
            updated[bookletId].status
          )
        }

        return updated
      })

      setBooklets(prev => {

        const updated = {

          ...prev

        }

        if (updated[bookletId]) {

          updated[bookletId] = {

            ...updated[bookletId],

            status: newStatus

          }

          if (

            selectedBooklet?.id === bookletId

          ) {

            setSelectedBooklet(
              updated[bookletId]
            )

            if (selectedPage) {

              const page =
                updated[bookletId]
                  .pages
                  .find(

                    p =>
                      p.page_number ===
                      selectedPage.page_number

                  )

              if (page) {

                setSelectedPage(page)

              }

            }

          }

        }

        return updated

      })

    } catch (err) {

      console.error(
        err
      )
    }
  }

  const createBooklet = ({
    bookletId,
    jobId,
    status = "REVIEW",
    reviewRequired = false,
    reasons = [],
    imageRoot = null,
    pages = []
  }) => ({

    id: bookletId,

    jobId,

    name: bookletId,

    status,

    review_required: reviewRequired,

    reasons,

    image_root: imageRoot,

    current_session: true,

    pages

  })

  const restoreBooklets = async () => {

    try {

      const response = await fetch("/jobs")

      const { jobs } = await response.json()

      const restoredBooklets = {}

      for (const job of Object.values(jobs)) {

        // Per-page data (image_path included) persisted as each page
        // finishes -- see job_manager.py's record_page, called from
        // processing_pipeline.py. Works for a job at ANY status
        // (still processing or completed), unlike the export JSON below,
        // which only exists once the job is done and never carried
        // image_path to begin with.
        const pageEntries =
          Object.values(job.pages || {})
            .sort((a, b) => a.page_number - b.page_number)

        const bookletId =
          job.booklet_id ||
          pageEntries[0]?.booklet_id ||
          job.job_id

        if (pageEntries.length > 0) {

          const latestPage =
            pageEntries[pageEntries.length - 1]

          restoredBooklets[bookletId] = createBooklet({

            bookletId,

            jobId: job.job_id,

            status: latestPage.status,

            reviewRequired: latestPage.review_required,

            reasons: latestPage.reasons || [],

            imageRoot: bookletId,

            pages: pageEntries.map(page => ({

              page_number: page.page_number,

              image_path: page.image_path,

              image_width: page.image_width,

              image_height: page.image_height,

              payload: page.payload

            }))

          })

          continue
        }

        // Fallback for manifests written before "pages" existed, or a
        // job that somehow finished without ever recording a page.
        // Restores booklet metadata and annotation text, but NOT images
        // -- the export JSON never included image_path.
        if (!job.export_path) {
          continue
        }

        try {

          const exportResponse =
            await fetch(
              `/jobs/${job.job_id}/export`
            )

          if (!exportResponse.ok) {
            continue
          }

          const exportData =
            await exportResponse.json()

          restoredBooklets[
            exportData.booklet_id
          ] = createBooklet({

            bookletId:
              exportData.booklet_id,

            jobId:
              exportData.job_id,

            status:
              exportData.status,

            reviewRequired:
              exportData.review_required,

            reasons:
              exportData.reasons || [],

            imageRoot:
              exportData.image_root,

            pages: exportData.pages.map(page => ({

              ...page,

              payload: {

                prediction_result: page.prediction_result,

                omr_result: page.omr_result,

                validation_result: page.validation_result

              }

            }))

          })

        } catch (err) {

          console.error(
            "FAILED TO LOAD EXPORT",
            job.job_id,
            err
          )

        }

      }

      setBooklets(prev => ({

        ...prev,

        ...restoredBooklets

      }))

    } catch (err) {

      console.error(
        "FAILED TO RESTORE BOOKLETS",
        err
      )

    }

  }
  useEffect(() => {

    document.documentElement
      .setAttribute(
        "data-theme",
        theme
      )

    localStorage.setItem(
      "theme",
      theme
    )

  }, [theme])

  useEffect(() => {

    let ws = null

    const initialize = async () => {

      await restoreBooklets()

      ws = connectWebSocket()

    }

    initialize()

    return () => {

      if (!ws) return

      ws.onclose = null
      ws.onerror = null

      if (

        ws.readyState === WebSocket.OPEN ||

        ws.readyState === WebSocket.CONNECTING

      ) {

        ws.close()

      }

    }

  }, [])

  useEffect(() => {

    const fetchHealth = async () => {

      try {

        const response =
          await fetch("/health")

        const data =
          await response.json()

        setServiceHealth(data)

      } catch {

        setServiceHealth({

          api: {
            healthy: false
          },

          redis: {
            healthy: false
          },

          gpu_worker: {
            healthy: false
          },

          telemetry: {
            healthy: false
          }
        })
      }
    }

    fetchHealth()

    const interval =
      setInterval(
        fetchHealth,
        5000
      )

    return () =>
      clearInterval(interval)

  }, [])

  return (

    <div className="app">

      <Header

        booklets={booklets}
        connectionStatus={connectionStatus}
        institutionName="Christ University"

        theme={theme}
        setTheme={setTheme}

        onSettingsClick={() =>

          setSettingsOpen(true)
        }
      />

      <Group
        direction="horizontal"
      >

        <Panel
          defaultSize={20}
          minSize={18}
        >

          <Sidebar

            booklets={booklets}
            selectedPage={
              selectedPage
            }

            setSelectedPage={
              setSelectedPage
            }

            setSelectedBooklet={
              setSelectedBooklet
            }

            updateBookletStatus={
              updateBookletStatus
            }
          />
        </Panel>

        <Separator />

        <Panel defaultSize={70}>

          <Viewer

            selectedPage={selectedPage}

            selectedBooklet={selectedBooklet}

            setSelectedPage={
              setSelectedPage
            }

            updateBookletStatus={updateBookletStatus}
          />

        </Panel>

      </Group>

      <Footer

        health={serviceHealth}

        websocketStatus={
          connectionStatus
        }

      />

      <SettingsDrawer

        open={settingsOpen}

        onClose={() =>

          setSettingsOpen(false)
        }
      />

    </div>
  )
}

export default App