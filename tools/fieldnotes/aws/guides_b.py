#!/usr/bin/env python3
"""AWS cost field notes, part two: EBS, snapshots, CloudWatch Logs, tagging."""

CITE_EBS = ("Amazon EBS pricing — AWS", "https://aws.amazon.com/ebs/pricing/")
CITE_CW = ("Amazon CloudWatch pricing — AWS", "https://aws.amazon.com/cloudwatch/pricing/")
CITE_TAGS = ("Organizing and tracking costs using AWS cost allocation tags — AWS Billing",
             "https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html")

GUIDES = [

{
"slug": "unattached-ebs-volumes",
"title": "Unattached EBS Volumes Bill Exactly Like Attached Ones",
"description": "Terminating an instance does not delete every volume it used. Whatever survives keeps billing at the full rate, and nothing on the console flags it.",
"h1": "unattached EBS volumes bill exactly like attached ones",
"category": "AWS cost",
"pill": "Cost",
"chips": ["EC2 API", "Python and Node.js", "Snapshot before delete"],
"keywords": ["unattached EBS volume", "orphaned EBS", "DeleteOnTermination",
             "gp2 gp3 cost", "AWS storage waste"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-ec2",
"lead": "An instance gets terminated. Its root volume goes with it, because <code>DeleteOnTermination</code> defaults to true for the root device. Any data volume attached later does not, because for those the default is the opposite. The volume survives in <code>available</code> state, holding data nobody will read again, and billing at <strong>$0.08 per GB-month for gp3</strong> exactly as if it were still doing work.",
"short_answer": """<p>An unattached EBS volume costs the same as an attached one. A forgotten 500 GB gp3 volume is <strong>$40 a month</strong>; gp2 is dearer still at $0.10/GB-month.</p>
<p><code>describe-volumes</code> with a status filter of <code>available</code> finds every one. The safe move is to snapshot before deleting &mdash; a snapshot of the same data costs $0.05/GB-month, so you keep a recoverable copy at a lower rate while you confirm nobody wanted it.</p>""",
"problem": """<p>The console shows the volume as <em>available</em>, which sounds like a resource ready for use rather than one quietly charging you. There is no warning, no age indicator on the cost, and no relationship shown to the instance that used to own it &mdash; that instance is gone.</p>
<p>The accumulation is steady rather than dramatic. Every terminated instance that had a data volume leaves one behind. A typical mid-size account carries five to fifteen of them, which lands somewhere between $50 and $200 a month of storage doing nothing.</p>""",
"why": """<p><strong>The default is inconsistent by device.</strong> Root volumes delete on termination; additional volumes attached afterwards do not. That inconsistency is defensible &mdash; data volumes usually hold something you want to keep &mdash; but it means the outcome depends on how the volume was attached, which nobody remembers a year later.</p>
<p><strong>Deleting feels irreversible, because it is.</strong> A volume might hold the only copy of something. Faced with that and no easy way to inspect the contents, the safe-feeling choice is to leave it, and leaving it is what costs money.</p>
<p><strong>gp2 volumes cost more and nobody migrates them.</strong> gp3 is roughly 20% cheaper than gp2 with better baseline performance, and the migration is live &mdash; no detach, no downtime. Old volumes sit on gp2 purely because changing them was never anybody's task.</p>""",
"steps": [
 {"h": "List what is unattached and how big it is",
  "body": """<p>Size is what determines cost, so sort by it. The oldest volumes are not necessarily the expensive ones.</p>
<pre><code class="language-bash">aws ec2 describe-volumes \\
  --filters Name=status,Values=available \\
  --query 'sort_by(Volumes,&Size)[].{Id:VolumeId,GB:Size,Type:VolumeType,Created:CreateTime}'</code></pre>"""},
 {"h": "Snapshot before you delete anything",
  "body": """<p>A snapshot of the same data costs $0.05/GB-month against $0.08 for the live gp3 volume, and it is restorable. Snapshot, wait for it to complete, then delete the volume: you have converted an expensive copy into a cheaper one without losing the option to go back.</p>"""},
 {"h": "Check the tags before assuming it is junk",
  "body": """<p>A volume tagged with an environment or an owner belongs to somebody. One with no tags at all and a creation date two years old is a much safer delete. The script reports tags alongside cost so the decision has something to go on.</p>"""},
 {"h": "Migrate what remains from gp2 to gp3",
  "body": """<p>For volumes still in use, <code>modify-volume</code> changes the type live. It is about 20% cheaper and generally faster, and the change needs no downtime.</p>
<pre><code class="language-bash">aws ec2 modify-volume --volume-id vol-0abc123 --volume-type gp3</code></pre>"""},
],
"verify": """<p>Confirm the snapshot completed before the volume disappears:</p>
<pre><code class="language-bash">aws ec2 describe-snapshots --snapshot-ids snap-0abc123 \\
  --query 'Snapshots[].{State:State,Progress:Progress}'
# State: completed

aws ec2 describe-volumes --filters Name=status,Values=available \\
  --query 'length(Volumes)'</code></pre>
<p>The count should drop and next month's EBS line should follow it.</p>""",
"code_intro": "The script lists unattached volumes with size, type, age and tags, and totals the monthly cost. Deletion takes a specific volume id, snapshots it first, and waits for the snapshot to complete before removing anything &mdash; because a delete you cannot undo deserves the extra minute.",
"py_file": "ebs_unattached_audit.py",
"py": '''"""Find unattached EBS volumes, cost them, and delete safely via a snapshot.

An unattached volume bills at the same rate as an attached one. Deletion is
irreversible, so this snapshots first and waits for the snapshot to complete
before removing anything.
"""
import argparse
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ebs_unattached_audit")

# us-east-1 list prices, August 2026.
PER_GB_MONTH = {"gp3": 0.08, "gp2": 0.10, "io1": 0.125, "io2": 0.125,
                "st1": 0.045, "sc1": 0.015, "standard": 0.05}
SNAPSHOT_PER_GB_MONTH = 0.05


def monthly_cost(volume):
    """Pure decision function: what this volume costs, and whether it is a safe delete.

    An untagged volume is a much safer delete than one carrying an owner or an
    environment, so that judgement is returned alongside the number.
    """
    size = volume.get("Size", 0)
    vtype = volume.get("VolumeType", "gp3")
    rate = PER_GB_MONTH.get(vtype, PER_GB_MONTH["gp3"])
    cost = size * rate
    tags = {t["Key"]: t["Value"] for t in volume.get("Tags", [])}
    confidence = "untagged, likely orphaned" if not tags else f"tagged {sorted(tags)}"
    saving_as_snapshot = cost - (size * SNAPSHOT_PER_GB_MONTH)
    return {"cost": cost, "confidence": confidence,
            "snapshot_saving": max(0.0, saving_as_snapshot), "tags": tags}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--delete", help="volume id to snapshot then delete")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ec2 = boto3.client("ec2", region_name=args.region)

    vols = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}])["Volumes"]
    total = 0.0
    for v in sorted(vols, key=lambda x: -x.get("Size", 0)):
        info = monthly_cost(v)
        total += info["cost"]
        log.warning("%s  %4d GB %-8s $%6.2f/mo  %s  (created %s)",
                    v["VolumeId"], v["Size"], v["VolumeType"], info["cost"],
                    info["confidence"], v["CreateTime"].date())
    if vols:
        log.warning("%d unattached volume(s) costing about $%.2f/month",
                    len(vols), total)
    else:
        log.info("no unattached volumes in %s", args.region)

    if args.delete:
        if not args.apply:
            log.info("WOULD snapshot then delete %s -- pass --apply", args.delete)
            return 0
        snap = ec2.create_snapshot(
            VolumeId=args.delete,
            Description=f"pre-delete safety copy of {args.delete}")
        log.info("snapshot %s started; waiting for it to complete", snap["SnapshotId"])
        ec2.get_waiter("snapshot_completed").wait(SnapshotIds=[snap["SnapshotId"]])
        ec2.delete_volume(VolumeId=args.delete)
        log.info("deleted %s -- restorable from %s", args.delete, snap["SnapshotId"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ebs-unattached-audit.mjs",
"js": '''/**
 * Find unattached EBS volumes, cost them, and delete safely via a snapshot.
 *
 * An unattached volume bills at the same rate as an attached one. Deletion is
 * irreversible, so this snapshots first and waits for completion.
 */
import {
  EC2Client,
  DescribeVolumesCommand,
  CreateSnapshotCommand,
  DeleteVolumeCommand,
  waitUntilSnapshotCompleted,
} from '@aws-sdk/client-ec2';

// us-east-1 list prices, August 2026.
const PER_GB_MONTH = {
  gp3: 0.08, gp2: 0.10, io1: 0.125, io2: 0.125, st1: 0.045, sc1: 0.015, standard: 0.05,
};
const SNAPSHOT_PER_GB_MONTH = 0.05;

/**
 * Pure decision function: what this volume costs, and whether it is a safe delete.
 * An untagged volume is a much safer delete than one carrying an owner.
 */
export function monthlyCost(volume) {
  const size = volume.Size ?? 0;
  const rate = PER_GB_MONTH[volume.VolumeType ?? 'gp3'] ?? PER_GB_MONTH.gp3;
  const cost = size * rate;
  const tags = Object.fromEntries((volume.Tags ?? []).map((t) => [t.Key, t.Value]));
  const keys = Object.keys(tags).sort();
  return {
    cost,
    confidence: keys.length ? `tagged ${JSON.stringify(keys)}` : 'untagged, likely orphaned',
    snapshotSaving: Math.max(0, cost - size * SNAPSHOT_PER_GB_MONTH),
    tags,
  };
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const apply = process.argv.includes('--apply');
  const toDelete = process.argv[process.argv.indexOf('--delete') + 1];
  const ec2 = new EC2Client({ region });

  const { Volumes = [] } = await ec2.send(new DescribeVolumesCommand({
    Filters: [{ Name: 'status', Values: ['available'] }],
  }));
  let total = 0;
  for (const v of [...Volumes].sort((a, b) => (b.Size ?? 0) - (a.Size ?? 0))) {
    const info = monthlyCost(v);
    total += info.cost;
    console.warn(`${v.VolumeId}  ${v.Size} GB ${v.VolumeType}  $${info.cost.toFixed(2)}/mo  ${info.confidence}`);
  }
  if (Volumes.length) {
    console.warn(`${Volumes.length} unattached volume(s) costing about $${total.toFixed(2)}/month`);
  } else {
    console.log(`no unattached volumes in ${region}`);
  }

  if (process.argv.includes('--delete')) {
    if (!apply) return console.log(`WOULD snapshot then delete ${toDelete} -- pass --apply`);
    const snap = await ec2.send(new CreateSnapshotCommand({
      VolumeId: toDelete, Description: `pre-delete safety copy of ${toDelete}`,
    }));
    console.log(`snapshot ${snap.SnapshotId} started; waiting`);
    await waitUntilSnapshotCompleted({ client: ec2, maxWaitTime: 900 },
      { SnapshotIds: [snap.SnapshotId] });
    await ec2.send(new DeleteVolumeCommand({ VolumeId: toDelete }));
    console.log(`deleted ${toDelete} -- restorable from ${snap.SnapshotId}`);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The pricing table and the tag heuristic are both worth pinning: an unknown volume type must not silently cost zero, and a tagged volume must never be described as orphaned.",
"test_py_file": "test_ebs_unattached_audit.py",
"test_py": '''from ebs_unattached_audit import monthly_cost


def test_gp3_pricing():
    assert monthly_cost({"Size": 500, "VolumeType": "gp3"})["cost"] == 40.0


def test_gp2_costs_more_than_gp3():
    gp2 = monthly_cost({"Size": 100, "VolumeType": "gp2"})["cost"]
    gp3 = monthly_cost({"Size": 100, "VolumeType": "gp3"})["cost"]
    assert gp2 > gp3


def test_unknown_type_falls_back_rather_than_costing_zero():
    """A new volume type must not silently report as free."""
    assert monthly_cost({"Size": 100, "VolumeType": "gp9"})["cost"] > 0


def test_untagged_volume_is_flagged_as_orphaned():
    assert "orphaned" in monthly_cost({"Size": 10, "VolumeType": "gp3"})["confidence"]


def test_tagged_volume_is_never_called_orphaned():
    info = monthly_cost({"Size": 10, "VolumeType": "gp3",
                         "Tags": [{"Key": "Owner", "Value": "platform"}]})
    assert "orphaned" not in info["confidence"]


def test_snapshot_is_cheaper_than_the_volume():
    assert monthly_cost({"Size": 100, "VolumeType": "gp3"})["snapshot_saving"] > 0
''',
"test_js_file": "ebs-unattached-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { monthlyCost } from './ebs-unattached-audit.mjs';

test('gp3 pricing', () => {
  assert.equal(monthlyCost({ Size: 500, VolumeType: 'gp3' }).cost, 40);
});

test('gp2 costs more than gp3', () => {
  assert.ok(monthlyCost({ Size: 100, VolumeType: 'gp2' }).cost
    > monthlyCost({ Size: 100, VolumeType: 'gp3' }).cost);
});

test('an unknown type falls back rather than costing zero', () => {
  assert.ok(monthlyCost({ Size: 100, VolumeType: 'gp9' }).cost > 0);
});

test('an untagged volume is flagged as orphaned', () => {
  assert.match(monthlyCost({ Size: 10, VolumeType: 'gp3' }).confidence, /orphaned/);
});

test('a tagged volume is never called orphaned', () => {
  const info = monthlyCost({ Size: 10, VolumeType: 'gp3', Tags: [{ Key: 'Owner', Value: 'p' }] });
  assert.doesNotMatch(info.confidence, /orphaned/);
});
''',
"faq": [
 ("Does an unattached volume really cost the same as an attached one?",
  "Yes. EBS bills for provisioned storage, not for use. A 500 GB gp3 volume is about $40 a month whether an instance is reading from it or nothing has touched it in a year."),
 ("Why did the volume survive when I terminated the instance?",
  "DeleteOnTermination defaults to true for the root device and false for volumes attached afterwards. The outcome depends on how the volume was attached, which is rarely remembered later."),
 ("Is it safe to delete an unattached volume?",
  "Only after you have a copy. Snapshot it first, wait for the snapshot to complete, then delete: a snapshot of the same data costs $0.05/GB-month against $0.08 for the live gp3 volume, so you keep a restorable copy at a lower rate."),
 ("Should I move gp2 volumes to gp3?",
  "Usually yes. gp3 is roughly 20% cheaper with better baseline performance, and modify-volume changes the type live with no detach and no downtime."),
 ("How much is typically sitting there?",
  "Five to fifteen unattached volumes is normal for a mid-size account, which lands somewhere between $50 and $200 a month. It accumulates one terminated instance at a time rather than arriving all at once."),
],
"related": [
 ("/aws/orphaned-ebs-snapshots/", "Orphaned EBS snapshots outlive the volumes they came from"),
 ("/aws/nat-gateway-idle-with-no-traffic/", "An idle NAT Gateway still costs $32 a month"),
 ("/aws/public-ipv4-now-always-charged/", "Public IPv4 is charged even when attached"),
],
"citations": [CITE_EBS,
 ("Amazon EBS volume types — AWS docs",
  "https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html"),
 ("boto3 ec2 describe_volumes",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_volumes.html")],
},

{
"slug": "orphaned-ebs-snapshots",
"title": "Orphaned EBS Snapshots Outlive the Volumes They Came From",
"description": "Deleting a volume does not delete its snapshots. They keep billing at $0.05 per GB-month, and nothing in AWS prunes them for you.",
"h1": "orphaned EBS snapshots outlive the volumes they came from",
"category": "AWS cost",
"pill": "Cost",
"chips": ["EC2 API", "Python and Node.js", "Incremental chains"],
"keywords": ["orphaned EBS snapshots", "EBS snapshot cost", "snapshot cleanup",
             "incremental snapshots", "AWS storage waste"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-ec2",
"lead": "Snapshots are the well-behaved part of EBS: incremental, cheap, easy to automate. That is exactly why they accumulate. A backup script from three years ago is still running. The volumes it protected were deleted long ago. Nothing in AWS notices the connection, so the snapshots remain, billing <strong>$0.05 per GB-month</strong> for a restore nobody will ever perform.",
"short_answer": """<p>Deleting a volume does not delete its snapshots, and AWS applies no default retention. A snapshot whose <code>VolumeId</code> no longer exists is orphaned and will bill forever.</p>
<p>Find them by listing snapshots you own, listing volumes, and taking the difference. Deleting is generally safe once the source volume is gone <em>and</em> no AMI references the snapshot &mdash; that second check is the one people skip, and it is what breaks a launch template months later.</p>""",
"problem": """<p>Nothing marks a snapshot as orphaned. The console shows a list with sizes and dates and a <code>VolumeId</code> that may point at something deleted years ago, with no indication that it does.</p>
<p>Because they are incremental, people assume they are nearly free. Each snapshot only stores blocks changed since the last one, which is true &mdash; but a chain of them collectively stores the full volume plus every change, and when the source volume is gone the chain still holds all of it.</p>""",
"why": """<p><strong>Automation outlives its purpose.</strong> A nightly snapshot job is set up once and rarely reviewed. It keeps running after the workload it protected is decommissioned, and it produces a new orphan every night.</p>
<p><strong>There is no default retention.</strong> Unlike some services, EBS snapshots do not expire. Data Lifecycle Manager can enforce retention but has to be configured deliberately, and typically is not until after somebody notices the bill.</p>
<p><strong>Deleting can break an AMI.</strong> An AMI is backed by snapshots. Delete one that an AMI depends on and the AMI stops being launchable &mdash; usually discovered by an autoscaling group at three in the morning. That real risk makes people avoid the whole job, which is how thousands accumulate.</p>""",
"steps": [
 {"h": "List every snapshot you own",
  "body": """<p><code>--owner-ids self</code> matters. Without it you get every public snapshot in the region, which is not what you want to be reading.</p>
<pre><code class="language-bash">aws ec2 describe-snapshots --owner-ids self \\
  --query 'Snapshots[].{Id:SnapshotId,Vol:VolumeId,GB:VolumeSize,When:StartTime}'</code></pre>"""},
 {"h": "Work out which source volumes still exist",
  "body": """<p>List current volume ids and subtract. A snapshot whose <code>VolumeId</code> is not in that set has no live source, which is the first condition for being orphaned.</p>"""},
 {"h": "Check no AMI depends on it — this is the step people skip",
  "body": """<p>Deregistered or not, an AMI backed by a snapshot needs that snapshot to launch. <code>describe-images --owners self</code> exposes the block device mappings; collect every snapshot id they reference and exclude those from deletion no matter how orphaned they look.</p>"""},
 {"h": "Keep a floor, then set up retention",
  "body": """<p>Deleting every orphan can leave you with no recovery point at all for a volume you deleted last week by mistake. Keep the most recent one per source volume, or anything under 30 days old. Then configure Data Lifecycle Manager so the problem stops regenerating.</p>"""},
],
"verify": """<p>Count before and after, and confirm nothing that an AMI needs went away:</p>
<pre><code class="language-bash">aws ec2 describe-snapshots --owner-ids self --query 'length(Snapshots)'

# every AMI should still be launchable
aws ec2 describe-images --owners self \\
  --query 'Images[].{Id:ImageId,State:State}'
# every State: available</code></pre>""",
"code_intro": "The script finds snapshots whose source volume no longer exists, excludes any referenced by an AMI, keeps anything newer than a cutoff you set, and totals the monthly cost of what is left. Deletion is per snapshot id and behind <code>--apply</code>.",
"py_file": "ebs_snapshot_orphans.py",
"py": '''"""Find EBS snapshots whose source volume is gone and no AMI depends on.

Snapshots do not expire and deleting a volume does not delete them, so they
accumulate one backup job at a time. The AMI check is the important part: an AMI
backed by a snapshot cannot launch without it, and that failure surfaces later,
usually in an autoscaling event.
"""
import argparse
import datetime as dt
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ebs_snapshot_orphans")

SNAPSHOT_PER_GB_MONTH = 0.05


def classify(snapshot, live_volume_ids, ami_snapshot_ids, min_age_days, now):
    """Pure decision function. Returns (deletable, reason).

    Three separate reasons to keep a snapshot, and they are checked in order of how
    badly deleting would hurt: an AMI dependency breaks launches, a live volume
    means it is a current backup, and a recent snapshot may be the only recovery
    point for something deleted by mistake.
    """
    if snapshot["SnapshotId"] in ami_snapshot_ids:
        return False, "an AMI depends on it"
    if snapshot.get("VolumeId") in live_volume_ids:
        return False, "source volume still exists"
    age = (now - snapshot["StartTime"]).days
    if age < min_age_days:
        return False, f"only {age} days old, inside the safety window"
    return True, f"source volume gone, {age} days old"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--min-age-days", type=int, default=30)
    ap.add_argument("--delete", help="snapshot id to delete")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ec2 = boto3.client("ec2", region_name=args.region)
    now = dt.datetime.now(dt.timezone.utc)

    live = {v["VolumeId"] for v in ec2.describe_volumes()["Volumes"]}
    ami_snaps = {
        m["Ebs"]["SnapshotId"]
        for img in ec2.describe_images(Owners=["self"])["Images"]
        for m in img.get("BlockDeviceMappings", [])
        if m.get("Ebs", {}).get("SnapshotId")
    }
    log.info("%d live volume(s), %d snapshot(s) referenced by an AMI",
             len(live), len(ami_snaps))

    total = 0.0
    for snap in ec2.describe_snapshots(OwnerIds=["self"])["Snapshots"]:
        deletable, reason = classify(snap, live, ami_snaps, args.min_age_days, now)
        cost = snap.get("VolumeSize", 0) * SNAPSHOT_PER_GB_MONTH
        if deletable:
            total += cost
            log.warning("ORPHAN %s  %3d GB  $%5.2f/mo  %s",
                        snap["SnapshotId"], snap.get("VolumeSize", 0), cost, reason)
    if total:
        log.warning("orphaned snapshots are costing about $%.2f/month", total)
    else:
        log.info("no orphaned snapshots older than %d days", args.min_age_days)

    if args.delete:
        if args.apply:
            ec2.delete_snapshot(SnapshotId=args.delete)
            log.info("deleted %s", args.delete)
        else:
            log.info("WOULD delete %s -- pass --apply", args.delete)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ebs-snapshot-orphans.mjs",
"js": '''/**
 * Find EBS snapshots whose source volume is gone and no AMI depends on.
 *
 * The AMI check is the important part: an AMI backed by a snapshot cannot launch
 * without it, and that failure surfaces later, usually in an autoscaling event.
 */
import {
  EC2Client,
  DescribeVolumesCommand,
  DescribeImagesCommand,
  DescribeSnapshotsCommand,
  DeleteSnapshotCommand,
} from '@aws-sdk/client-ec2';

const SNAPSHOT_PER_GB_MONTH = 0.05;

/**
 * Pure decision function. Returns { deletable, reason }.
 *
 * Checked in order of how badly deleting would hurt: an AMI dependency breaks
 * launches, a live volume means it is a current backup, and a recent snapshot may
 * be the only recovery point for something deleted by mistake.
 */
export function classify(snapshot, liveVolumeIds, amiSnapshotIds, minAgeDays, now) {
  if (amiSnapshotIds.has(snapshot.SnapshotId)) {
    return { deletable: false, reason: 'an AMI depends on it' };
  }
  if (liveVolumeIds.has(snapshot.VolumeId)) {
    return { deletable: false, reason: 'source volume still exists' };
  }
  const age = Math.floor((now - new Date(snapshot.StartTime)) / 86400_000);
  if (age < minAgeDays) {
    return { deletable: false, reason: `only ${age} days old, inside the safety window` };
  }
  return { deletable: true, reason: `source volume gone, ${age} days old` };
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const minAgeDays = Number(process.env.MIN_AGE_DAYS ?? 30);
  const apply = process.argv.includes('--apply');
  const toDelete = process.argv[process.argv.indexOf('--delete') + 1];
  const ec2 = new EC2Client({ region });
  const now = new Date();

  const { Volumes = [] } = await ec2.send(new DescribeVolumesCommand({}));
  const live = new Set(Volumes.map((v) => v.VolumeId));
  const { Images = [] } = await ec2.send(new DescribeImagesCommand({ Owners: ['self'] }));
  const amiSnaps = new Set(Images.flatMap((i) =>
    (i.BlockDeviceMappings ?? []).map((m) => m.Ebs?.SnapshotId).filter(Boolean)));
  console.log(`${live.size} live volume(s), ${amiSnaps.size} snapshot(s) referenced by an AMI`);

  const { Snapshots = [] } = await ec2.send(new DescribeSnapshotsCommand({ OwnerIds: ['self'] }));
  let total = 0;
  for (const snap of Snapshots) {
    const { deletable, reason } = classify(snap, live, amiSnaps, minAgeDays, now);
    if (!deletable) continue;
    const cost = (snap.VolumeSize ?? 0) * SNAPSHOT_PER_GB_MONTH;
    total += cost;
    console.warn(`ORPHAN ${snap.SnapshotId}  ${snap.VolumeSize} GB  $${cost.toFixed(2)}/mo  ${reason}`);
  }
  if (total) console.warn(`orphaned snapshots are costing about $${total.toFixed(2)}/month`);

  if (process.argv.includes('--delete')) {
    if (apply) {
      await ec2.send(new DeleteSnapshotCommand({ SnapshotId: toDelete }));
      console.log(`deleted ${toDelete}`);
    } else {
      console.log(`WOULD delete ${toDelete} -- pass --apply`);
    }
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "Three independent reasons to keep a snapshot, and the AMI one has to win even when every other signal says orphaned. That precedence is what the tests lock down.",
"test_py_file": "test_ebs_snapshot_orphans.py",
"test_py": '''import datetime as dt

from ebs_snapshot_orphans import classify

NOW = dt.datetime(2026, 8, 28, tzinfo=dt.timezone.utc)


def snap(days_old=365, vol="vol-gone", sid="snap-1", size=100):
    return {"SnapshotId": sid, "VolumeId": vol, "VolumeSize": size,
            "StartTime": NOW - dt.timedelta(days=days_old)}


def test_old_snapshot_with_no_volume_is_deletable():
    ok, _ = classify(snap(), set(), set(), 30, NOW)
    assert ok is True


def test_ami_dependency_wins_over_everything():
    """Even ancient, even with no source volume: deleting breaks the AMI."""
    ok, reason = classify(snap(days_old=2000), set(), {"snap-1"}, 30, NOW)
    assert ok is False
    assert "AMI" in reason


def test_live_source_volume_is_kept():
    ok, reason = classify(snap(vol="vol-live"), {"vol-live"}, set(), 30, NOW)
    assert ok is False
    assert "still exists" in reason


def test_recent_snapshot_is_inside_the_safety_window():
    ok, reason = classify(snap(days_old=5), set(), set(), 30, NOW)
    assert ok is False
    assert "safety window" in reason


def test_the_age_boundary():
    assert classify(snap(days_old=29), set(), set(), 30, NOW)[0] is False
    assert classify(snap(days_old=30), set(), set(), 30, NOW)[0] is True
''',
"test_js_file": "ebs-snapshot-orphans.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify } from './ebs-snapshot-orphans.mjs';

const NOW = new Date('2026-08-28T00:00:00Z');
const snap = ({ daysOld = 365, vol = 'vol-gone', sid = 'snap-1', size = 100 } = {}) => ({
  SnapshotId: sid, VolumeId: vol, VolumeSize: size,
  StartTime: new Date(NOW.getTime() - daysOld * 86400_000).toISOString(),
});

test('an old snapshot with no volume is deletable', () => {
  assert.equal(classify(snap(), new Set(), new Set(), 30, NOW).deletable, true);
});

test('an AMI dependency wins over everything', () => {
  const r = classify(snap({ daysOld: 2000 }), new Set(), new Set(['snap-1']), 30, NOW);
  assert.equal(r.deletable, false);
  assert.match(r.reason, /AMI/);
});

test('a live source volume is kept', () => {
  const r = classify(snap({ vol: 'vol-live' }), new Set(['vol-live']), new Set(), 30, NOW);
  assert.equal(r.deletable, false);
});

test('a recent snapshot is inside the safety window', () => {
  const r = classify(snap({ daysOld: 5 }), new Set(), new Set(), 30, NOW);
  assert.match(r.reason, /safety window/);
});
''',
"faq": [
 ("Are snapshots not almost free because they are incremental?",
  "Each snapshot stores only blocks changed since the last one, which is true. But a chain collectively holds the full volume plus every change, and when the source volume is deleted the chain still holds all of it, at $0.05 per GB-month indefinitely."),
 ("Does deleting a volume delete its snapshots?",
  "No, and there is no default retention either. Snapshots persist until something deletes them, which is why a backup job that outlived its workload produces a new orphan every night."),
 ("What is the risk in deleting one?",
  "An AMI backed by that snapshot stops being launchable. The failure usually surfaces later, in an autoscaling event, at an inconvenient hour. Always check describe-images for block device mappings before deleting, which is the step most cleanup scripts omit."),
 ("Why keep recent snapshots even when the volume is gone?",
  "Because a volume deleted last week might have been deleted by mistake, and the snapshot is the only way back. A 30-day floor costs very little and preserves that option."),
 ("How do I stop them accumulating again?",
  "Data Lifecycle Manager enforces retention policies on snapshots. Configuring it turns this from a recurring cleanup into a one-off, which is the actual fix."),
],
"related": [
 ("/aws/unattached-ebs-volumes/", "Unattached EBS volumes bill exactly like attached ones"),
 ("/aws/cloudwatch-logs-never-expire/", "CloudWatch log groups default to keeping everything forever"),
 ("/aws/nat-gateway-idle-with-no-traffic/", "An idle NAT Gateway still costs $32 a month"),
],
"citations": [CITE_EBS,
 ("Amazon EBS snapshots — AWS docs",
  "https://docs.aws.amazon.com/ebs/latest/userguide/ebs-snapshots.html"),
 ("Amazon Data Lifecycle Manager — AWS docs",
  "https://docs.aws.amazon.com/ebs/latest/userguide/snapshot-lifecycle.html")],
},

{
"slug": "cloudwatch-logs-never-expire",
"title": "CloudWatch Log Groups Keep Everything Forever by Default",
"description": "A new log group has no retention policy, so logs are kept indefinitely. Ingestion is $0.50 per GB and storage keeps accruing on data nobody will read.",
"h1": "CloudWatch log groups keep everything forever by default",
"category": "AWS cost",
"pill": "Cost",
"chips": ["CloudWatch Logs API", "Python and Node.js", "One call per group"],
"keywords": ["CloudWatch Logs retention", "never expire", "CloudWatch cost",
             "log group retention policy", "AWS logging cost"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-cloudwatch-logs",
"lead": "Every Lambda you have ever deployed created a log group. So did every ECS task definition and every API Gateway stage. None of them came with a retention policy, because the default is <strong>Never expire</strong>. Three years of debug output from a function you deleted in 2024 is still there, still stored, still billed &mdash; and setting retention is a single API call per group that nobody has ever run.",
"short_answer": """<p>New CloudWatch log groups default to <strong>Never expire</strong>. Ingestion is about $0.50/GB and storage about $0.03/GB-month in us-east-1, so the storage line grows every month and never falls.</p>
<p><code>PutRetentionPolicy</code> sets an expiry per group and applies to existing data, so one pass over your account can delete years of logs immediately. The script finds groups with no policy, reports what they are storing, and can set a retention you choose.</p>""",
"problem": """<p>Log groups are created for you, silently, by the services you use. Nobody sits down and decides to keep Lambda logs forever; it is simply what happens when nothing says otherwise.</p>
<p>The cost is split in a way that hides it. Ingestion is the larger charge and it is proportional to what you log, so it feels like a cost of doing business. Storage is small per GB but cumulative and permanent, which means it grows quietly and never shrinks. Groups belonging to deleted functions carry on billing with nothing generating new logs at all.</p>""",
"why": """<p><strong>The default is unlimited, and defaults win.</strong> Retention is an explicit setting on a resource you did not explicitly create, which is close to the worst case for something ever getting configured.</p>
<p><strong>Deleting a Lambda does not delete its log group.</strong> The function goes; <code>/aws/lambda/&lt;name&gt;</code> stays, holding everything it ever wrote. There is no cascade.</p>
<p><strong>The bill does not name the problem.</strong> CloudWatch charges appear as a single service total. Nothing says which of your several hundred log groups is responsible, and nothing indicates that most of them have no retention at all.</p>""",
"steps": [
 {"h": "Find groups with no retention policy",
  "body": """<p>A group with no <code>retentionInDays</code> key keeps data forever. That absence is the thing to look for.</p>
<pre><code class="language-bash">aws logs describe-log-groups \\
  --query 'logGroups[?retentionInDays==null].{Name:logGroupName,Bytes:storedBytes}'</code></pre>"""},
 {"h": "Sort by what they are actually storing",
  "body": """<p><code>storedBytes</code> tells you where the money is. A hundred empty groups cost nothing; one group holding 400 GB is the entire problem, and it is usually a debug-level logger somebody left on.</p>"""},
 {"h": "Choose retention by what the logs are for",
  "body": """<p>Different logs deserve different lifespans. Debug and application logs are rarely useful beyond a week or two; access logs may be wanted for a quarter; anything with an audit or compliance obligation has a period you do not get to choose. One blanket number across the account is easy but usually wrong at both ends.</p>"""},
 {"h": "Delete the groups whose source is gone",
  "body": """<p>A <code>/aws/lambda/</code> group for a function that no longer exists has no reason to survive at all. Setting retention on it still keeps the data for that period; deleting the group frees it now.</p>"""},
],
"verify": """<p>Confirm the policy applied and watch the stored bytes fall as expiry runs:</p>
<pre><code class="language-bash">aws logs describe-log-groups --log-group-name-prefix /aws/lambda/ \\
  --query 'logGroups[].{Name:logGroupName,Days:retentionInDays,Bytes:storedBytes}'

# nothing should still be null
aws logs describe-log-groups \\
  --query 'length(logGroups[?retentionInDays==null])'</code></pre>
<p>Deletion of expired data is not instant, so expect the stored total to drop over hours rather than immediately.</p>""",
"code_intro": "The script lists every log group with no retention policy, sorts by stored bytes so the expensive ones surface first, and estimates the monthly storage cost. Setting retention takes a day count and <code>--apply</code>; it can also target a prefix so you can treat Lambda logs differently from audit logs.",
"py_file": "cloudwatch_retention_audit.py",
"py": '''"""Find CloudWatch log groups with no retention policy and set one.

New log groups default to Never expire, and they are created for you by Lambda,
ECS and API Gateway rather than by anyone deciding to keep logs forever. Setting
retention applies to existing data, so one pass can free years of storage.
"""
import argparse
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudwatch_retention_audit")

STORAGE_PER_GB_MONTH = 0.03
# CloudWatch accepts only this set; anything else is rejected at the API.
VALID_RETENTION_DAYS = {1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400,
                        545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653}


def assess(group):
    """Pure decision function over one describe-log-groups entry."""
    stored = group.get("storedBytes", 0)
    gb = stored / 1_073_741_824
    return {
        "unbounded": "retentionInDays" not in group,
        "gb": gb,
        "monthly_usd": gb * STORAGE_PER_GB_MONTH,
        "orphan_hint": group.get("logGroupName", "").startswith("/aws/lambda/"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--prefix", default="", help="only groups starting with this")
    ap.add_argument("--set-days", type=int, help="retention to apply")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.set_days and args.set_days not in VALID_RETENTION_DAYS:
        log.error("%d is not an accepted retention; choose one of %s",
                  args.set_days, sorted(VALID_RETENTION_DAYS))
        return 2

    logs = boto3.client("logs", region_name=args.region)
    paginator = logs.get_paginator("describe_log_groups")
    kwargs = {"logGroupNamePrefix": args.prefix} if args.prefix else {}

    unbounded, total = [], 0.0
    for page in paginator.paginate(**kwargs):
        for g in page["logGroups"]:
            info = assess(g)
            if info["unbounded"]:
                unbounded.append((g["logGroupName"], info))
                total += info["monthly_usd"]

    for name, info in sorted(unbounded, key=lambda x: -x[1]["gb"])[:40]:
        log.warning("NO RETENTION  %7.2f GB  $%5.2f/mo  %s", info["gb"],
                    info["monthly_usd"], name)
    if unbounded:
        log.warning("%d group(s) keep logs forever, about $%.2f/month in storage",
                    len(unbounded), total)
    else:
        log.info("every log group has a retention policy")

    if args.set_days and args.apply:
        for name, _ in unbounded:
            logs.put_retention_policy(logGroupName=name, retentionInDays=args.set_days)
        log.info("set %d-day retention on %d group(s)", args.set_days, len(unbounded))
    elif args.set_days:
        log.info("WOULD set %d-day retention on %d group(s) -- pass --apply",
                 args.set_days, len(unbounded))
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "cloudwatch-retention-audit.mjs",
"js": '''/**
 * Find CloudWatch log groups with no retention policy and set one.
 *
 * New log groups default to Never expire, and they are created for you by Lambda,
 * ECS and API Gateway rather than by anyone deciding to keep logs forever.
 */
import {
  CloudWatchLogsClient,
  DescribeLogGroupsCommand,
  PutRetentionPolicyCommand,
} from '@aws-sdk/client-cloudwatch-logs';

const STORAGE_PER_GB_MONTH = 0.03;
// CloudWatch accepts only this set; anything else is rejected at the API.
export const VALID_RETENTION_DAYS = new Set([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180,
  365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653]);

/** Pure decision function over one describe-log-groups entry. */
export function assess(group) {
  const gb = (group.storedBytes ?? 0) / 1_073_741_824;
  return {
    unbounded: group.retentionInDays === undefined,
    gb,
    monthlyUsd: gb * STORAGE_PER_GB_MONTH,
    orphanHint: (group.logGroupName ?? '').startsWith('/aws/lambda/'),
  };
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const apply = process.argv.includes('--apply');
  const setDays = Number(process.argv[process.argv.indexOf('--set-days') + 1]);
  if (process.argv.includes('--set-days') && !VALID_RETENTION_DAYS.has(setDays)) {
    console.error(`${setDays} is not an accepted retention value`);
    process.exit(2);
  }
  const client = new CloudWatchLogsClient({ region });

  const unbounded = [];
  let total = 0;
  let nextToken;
  do {
    const page = await client.send(new DescribeLogGroupsCommand({ nextToken }));
    for (const g of page.logGroups ?? []) {
      const info = assess(g);
      if (info.unbounded) { unbounded.push([g.logGroupName, info]); total += info.monthlyUsd; }
    }
    nextToken = page.nextToken;
  } while (nextToken);

  for (const [name, info] of unbounded.sort((a, b) => b[1].gb - a[1].gb).slice(0, 40)) {
    console.warn(`NO RETENTION  ${info.gb.toFixed(2)} GB  $${info.monthlyUsd.toFixed(2)}/mo  ${name}`);
  }
  if (unbounded.length) {
    console.warn(`${unbounded.length} group(s) keep logs forever, about $${total.toFixed(2)}/month`);
  }

  if (process.argv.includes('--set-days')) {
    if (apply) {
      for (const [name] of unbounded) {
        await client.send(new PutRetentionPolicyCommand({
          logGroupName: name, retentionInDays: setDays }));
      }
      console.log(`set ${setDays}-day retention on ${unbounded.length} group(s)`);
    } else {
      console.log(`WOULD set ${setDays}-day retention on ${unbounded.length} group(s) -- pass --apply`);
    }
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "Two things are easy to get wrong: a retention of zero is not the same as no retention, and CloudWatch only accepts a fixed set of day values, so a sensible-looking 45 is rejected at the API.",
"test_py_file": "test_cloudwatch_retention_audit.py",
"test_py": '''from cloudwatch_retention_audit import assess, VALID_RETENTION_DAYS


def test_missing_key_means_unbounded():
    assert assess({"logGroupName": "/aws/lambda/x", "storedBytes": 0})["unbounded"] is True


def test_a_retention_of_any_value_is_bounded():
    g = {"logGroupName": "/x", "storedBytes": 0, "retentionInDays": 7}
    assert assess(g)["unbounded"] is False


def test_cost_scales_with_stored_bytes():
    ten_gb = 10 * 1_073_741_824
    assert round(assess({"logGroupName": "/x", "storedBytes": ten_gb})["monthly_usd"], 2) == 0.30


def test_lambda_groups_are_hinted_as_likely_orphans():
    assert assess({"logGroupName": "/aws/lambda/gone", "storedBytes": 1})["orphan_hint"]


def test_45_days_is_not_an_accepted_retention():
    """Looks reasonable, rejected by the API. Worth failing early on."""
    assert 45 not in VALID_RETENTION_DAYS
    assert 30 in VALID_RETENTION_DAYS and 60 in VALID_RETENTION_DAYS
''',
"test_js_file": "cloudwatch-retention-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assess, VALID_RETENTION_DAYS } from './cloudwatch-retention-audit.mjs';

test('a missing key means unbounded', () => {
  assert.equal(assess({ logGroupName: '/aws/lambda/x', storedBytes: 0 }).unbounded, true);
});

test('any retention value means bounded', () => {
  assert.equal(assess({ logGroupName: '/x', storedBytes: 0, retentionInDays: 7 }).unbounded, false);
});

test('cost scales with stored bytes', () => {
  const tenGb = 10 * 1_073_741_824;
  assert.equal(assess({ logGroupName: '/x', storedBytes: tenGb }).monthlyUsd.toFixed(2), '0.30');
});

test('45 days is not an accepted retention', () => {
  assert.equal(VALID_RETENTION_DAYS.has(45), false);
  assert.ok(VALID_RETENTION_DAYS.has(30) && VALID_RETENTION_DAYS.has(60));
});
''',
"faq": [
 ("What is the default retention for a CloudWatch log group?",
  "Never expire. Logs are kept indefinitely unless a retention policy is set, and the groups are created for you by Lambda, ECS and API Gateway rather than by anyone choosing to keep them forever."),
 ("Does setting retention delete logs already stored?",
  "Yes. The policy applies to existing data, so a single pass over an account can free years of storage. Deletion is not instant — expect stored bytes to fall over hours rather than immediately."),
 ("Does deleting a Lambda delete its log group?",
  "No. The function goes and /aws/lambda/<name> stays, holding everything it ever wrote. There is no cascade, which is why accounts accumulate log groups for code that no longer exists."),
 ("Can I set any number of days?",
  "No. CloudWatch accepts a fixed set — 1, 3, 5, 7, 14, 30, 60, 90 and so on. A reasonable-looking 45 is rejected at the API, which is why the script validates before it starts."),
 ("Which costs more, ingestion or storage?",
  "Ingestion, at roughly $0.50/GB against $0.03/GB-month for storage. But ingestion is proportional to what you log while storage is cumulative and permanent, so retention is what stops the second one growing forever."),
],
"related": [
 ("/aws/orphaned-ebs-snapshots/", "Orphaned EBS snapshots outlive their volumes"),
 ("/aws/untagged-resources-break-cost-attribution/", "Untagged resources break cost attribution"),
 ("/aws/nat-gateway-idle-with-no-traffic/", "An idle NAT Gateway still costs $32 a month"),
],
"citations": [CITE_CW,
 ("Working with log groups and log streams — AWS docs",
  "https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html"),
 ("boto3 logs put_retention_policy",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs/client/put_retention_policy.html")],
},

{
"slug": "untagged-resources-break-cost-attribution",
"title": "Untagged Resources Make Cost Attribution Impossible",
"description": "Cost Explorer can only group by tags you activated in the billing console. Untagged resources land in a bucket nobody can attribute to a team or a customer.",
"h1": "untagged resources make cost attribution impossible",
"category": "AWS cost",
"pill": "Governance",
"chips": ["Resource Groups Tagging API", "Python and Node.js", "Two-step activation"],
"keywords": ["AWS cost allocation tags", "untagged resources", "Cost Explorer grouping",
             "activate cost allocation tags", "AWS tagging strategy"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-resource-groups-tagging-api",
"lead": "Somebody asks what a customer costs to serve, or which team is responsible for the biggest line on the bill, and there is no way to answer. Cost Explorer can group by tag &mdash; but only tags that were applied to resources <em>and</em> activated in the billing console, and only from the point of activation onward. Miss either step and the question stays unanswerable no matter how much data accumulates.",
"short_answer": """<p>Cost allocation needs two things, and people usually do only the first. <strong>Tag the resources</strong>, then <strong>activate the tag keys</strong> in Billing &rarr; Cost allocation tags. An activated key only applies to costs incurred afterwards, so this is not retroactive.</p>
<p>The Resource Groups Tagging API can list every resource missing a required key, and tag them in bulk. Activation itself is a billing-console action with a lag: up to 24 hours for a key to appear, and up to another 24 to activate.</p>""",
"problem": """<p>The bill is a single number per service. Without tags, "what does this customer cost" and "which team owns this spend" have no answer, and the usual substitute &mdash; guessing from resource names &mdash; falls apart the moment naming conventions diverge, which they always do.</p>
<p>The trap that wastes the most time is the second step. Teams tag diligently, wait a month, open Cost Explorer, and find the tag is not available as a grouping dimension. The tags are on the resources; they were never activated for billing, and the month that has passed cannot be recovered.</p>""",
"why": """<p><strong>Tagging and activating are separate systems.</strong> One is a resource-level API, the other a billing-console setting. Nothing connects them, and nothing warns that tagging alone achieves nothing for cost reporting.</p>
<p><strong>Activation is not retroactive.</strong> Cost data before activation carries no tag dimension and never will. The longer the gap between tagging and activating, the more history is permanently unattributable.</p>
<p><strong>Resources are created faster than they are tagged.</strong> Console clicks, Terraform without default tags, an SDK call in a script &mdash; each creates something untagged unless someone remembered. Compliance decays without enforcement.</p>""",
"steps": [
 {"h": "Decide the small set of keys that matter",
  "body": """<p>Three or four is plenty: an owner, an environment, a cost centre or customer, and perhaps a service. A long list guarantees inconsistent application, and inconsistent tags are as useless as none.</p>"""},
 {"h": "Find what is missing them",
  "body": """<p>The Resource Groups Tagging API covers most taggable resources in one call, which is far better than walking every service API.</p>
<pre><code class="language-bash">aws resourcegroupstaggingapi get-resources \\
  --query 'ResourceTagMappingList[?length(Tags)==`0`].ResourceARN'</code></pre>"""},
 {"h": "Tag in bulk, then activate — and do not skip the second half",
  "body": """<p><code>tag-resources</code> takes up to 20 ARNs at a time. Once tagged, go to <em>Billing &rarr; Cost allocation tags</em>, select the keys and activate them. Nothing in the API does this for you, and until it is done Cost Explorer cannot group by them.</p>"""},
 {"h": "Enforce it so it does not decay",
  "body": """<p>Terraform <code>default_tags</code> at the provider level tags everything it creates. An AWS Config rule or a Service Control Policy can flag or block untagged resources. Without enforcement, compliance drifts back down within a quarter.</p>"""},
],
"verify": """<p>Check the untagged count fell, then confirm the key is actually usable for billing:</p>
<pre><code class="language-bash">aws resourcegroupstaggingapi get-resources \\
  --query 'length(ResourceTagMappingList[?length(Tags)==`0`])'</code></pre>
<p>Then open Cost Explorer and try grouping by the tag. If it is not offered, activation has not completed &mdash; it can take 24 hours to appear and another 24 to activate.</p>""",
"code_intro": "The script reports tag coverage across every taggable resource, broken down by required key and by service so you can see where the gaps cluster. Bulk tagging takes an explicit key, value and <code>--apply</code>. It cannot activate tags for billing &mdash; that is console-only &mdash; so it ends by telling you to go and do it.",
"py_file": "aws_tag_coverage.py",
"py": '''"""Report cost-allocation tag coverage and bulk-tag what is missing.

Two steps are needed and people usually do only the first: tag the resources, then
ACTIVATE the tag keys in Billing -> Cost allocation tags. Activation is not
retroactive, so every day between tagging and activating is a day of spend that can
never be attributed.
"""
import argparse
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("aws_tag_coverage")

DEFAULT_REQUIRED = ["Owner", "Environment", "CostCentre"]


def coverage(resources, required):
    """Pure decision function. Returns per-key counts and the untagged ARNs.

    Counts a key as present only when it has a non-empty value: an empty string is
    worse than no tag, because it looks compliant in a report and groups into a
    blank bucket in Cost Explorer.
    """
    missing = {k: [] for k in required}
    fully_untagged = []
    for r in resources:
        tags = {t["Key"]: t.get("Value", "") for t in r.get("Tags", [])}
        if not tags:
            fully_untagged.append(r["ResourceARN"])
        for key in required:
            if not tags.get(key, "").strip():
                missing[key].append(r["ResourceARN"])
    return {
        "total": len(resources),
        "fully_untagged": fully_untagged,
        "missing_by_key": missing,
    }


def service_of(arn):
    parts = arn.split(":")
    return parts[2] if len(parts) > 2 else "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--required", nargs="+", default=DEFAULT_REQUIRED)
    ap.add_argument("--tag-key")
    ap.add_argument("--tag-value")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    api = boto3.client("resourcegroupstaggingapi", region_name=args.region)
    resources = []
    for page in api.get_paginator("get_resources").paginate():
        resources += page["ResourceTagMappingList"]

    c = coverage(resources, args.required)
    log.info("%d taggable resource(s) in %s", c["total"], args.region)
    for key, arns in c["missing_by_key"].items():
        pct = 100 * (1 - len(arns) / c["total"]) if c["total"] else 100
        log.warning("  %-14s %5.1f%% covered, %d missing", key, pct, len(arns))

    if c["fully_untagged"]:
        by_service = {}
        for arn in c["fully_untagged"]:
            by_service[service_of(arn)] = by_service.get(service_of(arn), 0) + 1
        log.warning("  %d resource(s) have no tags at all: %s",
                    len(c["fully_untagged"]),
                    ", ".join(f"{k}={v}" for k, v in sorted(
                        by_service.items(), key=lambda x: -x[1])[:6]))

    if args.tag_key and args.tag_value:
        targets = c["missing_by_key"].get(args.tag_key, [])
        if args.apply:
            for i in range(0, len(targets), 20):     # the API caps at 20 ARNs
                api.tag_resources(ResourceARNList=targets[i:i + 20],
                                  Tags={args.tag_key: args.tag_value})
            log.info("tagged %d resource(s) with %s=%s",
                     len(targets), args.tag_key, args.tag_value)
        else:
            log.info("WOULD tag %d resource(s) with %s=%s -- pass --apply",
                     len(targets), args.tag_key, args.tag_value)

    log.info("REMINDER: tagging alone does nothing for cost reporting. Activate the "
             "keys in Billing -> Cost allocation tags. It is not retroactive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "aws-tag-coverage.mjs",
"js": '''/**
 * Report cost-allocation tag coverage and bulk-tag what is missing.
 *
 * Two steps are needed and people usually do only the first: tag the resources,
 * then ACTIVATE the tag keys in Billing -> Cost allocation tags. Activation is not
 * retroactive.
 */
import {
  ResourceGroupsTaggingAPIClient,
  GetResourcesCommand,
  TagResourcesCommand,
} from '@aws-sdk/client-resource-groups-tagging-api';

const DEFAULT_REQUIRED = ['Owner', 'Environment', 'CostCentre'];

/**
 * Pure decision function. Returns per-key counts and the untagged ARNs.
 *
 * Counts a key as present only when it has a non-empty value: an empty string is
 * worse than no tag, because it looks compliant and groups into a blank bucket.
 */
export function coverage(resources, required) {
  const missing = Object.fromEntries(required.map((k) => [k, []]));
  const fullyUntagged = [];
  for (const r of resources) {
    const tags = Object.fromEntries((r.Tags ?? []).map((t) => [t.Key, t.Value ?? '']));
    if (!Object.keys(tags).length) fullyUntagged.push(r.ResourceARN);
    for (const key of required) {
      if (!(tags[key] ?? '').trim()) missing[key].push(r.ResourceARN);
    }
  }
  return { total: resources.length, fullyUntagged, missingByKey: missing };
}

const serviceOf = (arn) => arn.split(':')[2] ?? 'unknown';

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const apply = process.argv.includes('--apply');
  const tagKey = process.argv[process.argv.indexOf('--tag-key') + 1];
  const tagValue = process.argv[process.argv.indexOf('--tag-value') + 1];
  const api = new ResourceGroupsTaggingAPIClient({ region });

  const resources = [];
  let PaginationToken;
  do {
    const page = await api.send(new GetResourcesCommand({ PaginationToken }));
    resources.push(...(page.ResourceTagMappingList ?? []));
    PaginationToken = page.PaginationToken || undefined;
  } while (PaginationToken);

  const c = coverage(resources, DEFAULT_REQUIRED);
  console.log(`${c.total} taggable resource(s) in ${region}`);
  for (const [key, arns] of Object.entries(c.missingByKey)) {
    const pct = c.total ? 100 * (1 - arns.length / c.total) : 100;
    console.warn(`  ${key.padEnd(14)} ${pct.toFixed(1)}% covered, ${arns.length} missing`);
  }
  if (c.fullyUntagged.length) {
    const byService = {};
    for (const arn of c.fullyUntagged) byService[serviceOf(arn)] = (byService[serviceOf(arn)] ?? 0) + 1;
    console.warn(`  ${c.fullyUntagged.length} resource(s) have no tags at all:`,
      Object.entries(byService).sort((a, b) => b[1] - a[1]).slice(0, 6));
  }

  if (process.argv.includes('--tag-key')) {
    const targets = c.missingByKey[tagKey] ?? [];
    if (apply) {
      for (let i = 0; i < targets.length; i += 20) {   // the API caps at 20 ARNs
        await api.send(new TagResourcesCommand({
          ResourceARNList: targets.slice(i, i + 20), Tags: { [tagKey]: tagValue } }));
      }
      console.log(`tagged ${targets.length} resource(s) with ${tagKey}=${tagValue}`);
    } else {
      console.log(`WOULD tag ${targets.length} with ${tagKey}=${tagValue} -- pass --apply`);
    }
  }

  console.log('REMINDER: tagging alone does nothing for cost reporting. Activate the '
    + 'keys in Billing -> Cost allocation tags. It is not retroactive.');
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The rule worth testing is that an empty tag value does not count as coverage. A blank value is worse than a missing tag: it reads as compliant in a report and groups into an unlabelled bucket in Cost Explorer.",
"test_py_file": "test_aws_tag_coverage.py",
"test_py": '''from aws_tag_coverage import coverage

REQUIRED = ["Owner", "Environment"]


def res(arn, **tags):
    return {"ResourceARN": arn, "Tags": [{"Key": k, "Value": v} for k, v in tags.items()]}


def test_fully_tagged_resource_is_covered():
    c = coverage([res("arn:aws:ec2:::i-1", Owner="team", Environment="prod")], REQUIRED)
    assert c["missing_by_key"]["Owner"] == []
    assert c["fully_untagged"] == []


def test_an_empty_value_does_not_count_as_covered():
    """A blank value reads as compliant and groups into an unlabelled bucket."""
    c = coverage([res("arn:aws:ec2:::i-1", Owner="", Environment="prod")], REQUIRED)
    assert len(c["missing_by_key"]["Owner"]) == 1


def test_whitespace_only_is_also_missing():
    c = coverage([res("arn:aws:ec2:::i-1", Owner="   ", Environment="prod")], REQUIRED)
    assert len(c["missing_by_key"]["Owner"]) == 1


def test_a_resource_with_no_tags_is_counted_once_per_key():
    c = coverage([{"ResourceARN": "arn:aws:s3:::bucket", "Tags": []}], REQUIRED)
    assert len(c["fully_untagged"]) == 1
    assert len(c["missing_by_key"]["Owner"]) == 1
    assert len(c["missing_by_key"]["Environment"]) == 1


def test_empty_account_does_not_divide_by_zero():
    assert coverage([], REQUIRED)["total"] == 0
''',
"test_js_file": "aws-tag-coverage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { coverage } from './aws-tag-coverage.mjs';

const REQUIRED = ['Owner', 'Environment'];
const res = (arn, tags) => ({
  ResourceARN: arn,
  Tags: Object.entries(tags).map(([Key, Value]) => ({ Key, Value })),
});

test('a fully tagged resource is covered', () => {
  const c = coverage([res('arn:aws:ec2:::i-1', { Owner: 'team', Environment: 'prod' })], REQUIRED);
  assert.deepEqual(c.missingByKey.Owner, []);
});

test('an empty value does not count as covered', () => {
  const c = coverage([res('arn:aws:ec2:::i-1', { Owner: '', Environment: 'prod' })], REQUIRED);
  assert.equal(c.missingByKey.Owner.length, 1);
});

test('whitespace only is also missing', () => {
  const c = coverage([res('arn:aws:ec2:::i-1', { Owner: '   ', Environment: 'prod' })], REQUIRED);
  assert.equal(c.missingByKey.Owner.length, 1);
});

test('a resource with no tags is counted once per key', () => {
  const c = coverage([{ ResourceARN: 'arn:aws:s3:::b', Tags: [] }], REQUIRED);
  assert.equal(c.fullyUntagged.length, 1);
  assert.equal(c.missingByKey.Owner.length, 1);
});
''',
"faq": [
 ("I tagged everything but Cost Explorer will not group by my tag. Why?",
  "Tagging and activating are separate steps. The tag key has to be activated in Billing → Cost allocation tags before it becomes a grouping dimension. Nothing in the tagging API does this, and nothing warns you."),
 ("Is activation retroactive?",
  "No. An activated key only applies to costs incurred after activation. Spend before that point carries no tag dimension and never will, so the gap between tagging and activating is permanently unattributable."),
 ("How long does activation take?",
  "Up to 24 hours for a newly used tag key to appear in the cost allocation tags page, and up to another 24 hours for it to activate after you select it. Two days is normal; assume it is broken only after that."),
 ("How many tag keys should I require?",
  "Three or four. An owner, an environment, a cost centre or customer, perhaps a service. Long lists get applied inconsistently, and inconsistent tags are as useless for attribution as none."),
 ("How do I stop coverage decaying?",
  "Enforce at creation. Terraform default_tags at the provider level tags everything it creates; an AWS Config rule or a Service Control Policy can flag or block untagged resources. Without enforcement, coverage drifts back down within a quarter."),
],
"related": [
 ("/aws/cloudwatch-logs-never-expire/", "CloudWatch log groups keep everything forever"),
 ("/aws/unattached-ebs-volumes/", "Unattached EBS volumes bill like attached ones"),
 ("/aws/nat-gateway-idle-with-no-traffic/", "An idle NAT Gateway still costs $32 a month"),
],
"citations": [CITE_TAGS,
 ("Activating user-defined cost allocation tags — AWS Billing",
  "https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html"),
 ("Resource Groups Tagging API reference — AWS docs",
  "https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/overview.html")],
},

]
