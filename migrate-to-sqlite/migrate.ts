import UserInfoData from "./data/user_info.json"
import ChallengeData from "./data/challenge.json"
import EventData from "./data/event.json"
import CompetitionData from "./data/competition.json"
import ConfigData from "./data/config.json"
import UserEventHistoryData from "./data/user_event_history.json"

import {ChallengeTemplate, PrismaClient} from "@prisma/client"
import { objectIdToDate } from "./utils/object-id-to-unix.js"
import { createIdMap } from "./utils/create-map.js"


const prisma = new PrismaClient()

{
    const counts: Record<string, number> = {}
    UserInfoData.forEach(u=>{
        counts[u.mail] = (counts[u.mail] ?? 0) + 1
    })
    Object.entries(counts).forEach(([k, v])=>{
        if(v > 1) {
            console.log(k);
            process.exit(1);
        }
    })
}

await prisma.user.deleteMany()
const userIdMap = createIdMap()

for(const {username, no, mail, psw, _id} of UserInfoData) {
    const res = await prisma.user.create({
        data: {
            username,
            no,
            email: mail,
            password: psw,
            permission: undefined,
            ctime: objectIdToDate(_id),
        }
    })
    userIdMap[_id] = res.id
}


await prisma.challengeTemplate.deleteMany()
const challengeIdMap = createIdMap()
const challengeDataMap: Record<string, ChallengeTemplate> = {}
for(const c of ChallengeData) {
    const res = await prisma.challengeTemplate.create({
        data: {
            ctime: objectIdToDate(c._id),
            creatorId: userIdMap[c.uid],
            description: c.desc,
            title: c.title,
            label: c.label,
            flag: c.flag
        }
    })
    challengeIdMap[c._id] = res.id
    challengeDataMap[c._id] = res
}

await prisma.event.deleteMany()
const eventsIdMap = createIdMap()
for(const e of EventData) {
    const res = await prisma.event.create({
        data: {
            creatorId: userIdMap[e.uid],
            ctime: objectIdToDate(e._id),
            title: e.title,
            detail: e.desc,
            organizer: e.organizer,
            startTime: new Date(e.start),
            endTime: new Date(e.end),
            isCompetition: e.is_competition,
            roll: {
                createMany: {
                    data: e.roll.map(d=>({
                        userId: userIdMap[d]
                    })).filter(d=>!!d)
                }
            },
        }
    })
    eventsIdMap[e._id] = res.id
}

const challengeTemplateIdMap = createIdMap()
for(const {_id, title, desc, flag, label, uid} of ChallengeData) {
    const res = await prisma.challengeTemplate.create({
        data: {
            creatorId: userIdMap[uid],
            title: title,
            description: desc,
            flag: flag,
            label: label,
            ctime: objectIdToDate(_id),
            mtime: objectIdToDate(_id),
        }
    })
    challengeTemplateIdMap[_id] = res.id
}

for(const {challenges, _id: competitionId} of CompetitionData) {
    // create shadow competition
    const competition = await prisma.shadowCompetition.create({
        data: {
            eventId: eventsIdMap[competitionId],
            ctime: objectIdToDate(competitionId),
            mtime: objectIdToDate(competitionId)
        }
    })
    for(const {id: challengeId, passed, score} of challenges) {
        const {title, flag, description} = challengeDataMap[challengeId]
        const challengeInstance = await prisma.competitionChallengeInstance.create({
            data:{
                competitionId: competition.eventId,
                templateId: challengeTemplateIdMap[challengeId],
                title,
                flag,
                description,
                score,
                ctime: objectIdToDate(challengeId),
                mtime: objectIdToDate(challengeId),
            }
        })
        for(const {time, id: userId} of passed) {
            await prisma.competitionScoreboard.create({
                data: {
                    competitionId: competition.eventId,
                    challengeId: challengeInstance.id,
                    userId: userIdMap[userId],
                    ctime: new Date(time)
                }
            }).catch(()=>{})
        }
    }
}

process.exit(0)
