#!/usr/bin/env python3
"""AWS cost field notes, part one: NAT gateways, public IPv4, unattached EBS.

Every figure here was checked against the AWS pricing pages in August 2026 and is
cited on the page. They are us-east-1 list rates; other regions differ, which the
pages say rather than pretending otherwise.
"""

CITE_NAT = ("Amazon VPC pricing — AWS", "https://aws.amazon.com/vpc/pricing/")
CITE_EC2 = ("Amazon EC2 On-Demand pricing — AWS", "https://aws.amazon.com/ec2/pricing/on-demand/")
CITE_EBS = ("Amazon EBS pricing — AWS", "https://aws.amazon.com/ebs/pricing/")
CITE_IPV4 = ("New — AWS public IPv4 address charge + Public IP Insights — AWS News Blog",
             "https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights")

GUIDES = [

{
"slug": "nat-gateway-idle-with-no-traffic",
"title": "An Idle NAT Gateway Still Costs $32 a Month",
"description": "A NAT Gateway bills per hour whether or not a single byte crosses it. One left behind after a VPC redesign is about $32 a month for nothing.",
"h1": "an idle NAT Gateway still costs about $32 a month",
"category": "AWS cost",
"pill": "Cost",
"chips": ["EC2 and CloudWatch APIs", "Python and Node.js", "Dry run by default"],
"keywords": ["NAT Gateway cost", "idle NAT Gateway", "AWS zombie resources",
             "VPC endpoint vs NAT Gateway", "AWS cost optimisation"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-ec2",
"lead": "Someone built a private subnet, needed outbound internet for one task, and created a NAT Gateway. The task moved to a different account, or the workload was replaced by something using VPC endpoints, and the gateway stayed. It has no traffic. It has had no traffic for months. At <strong>$0.045 per gateway-hour</strong> it is still billing about <strong>$32 a month</strong>, and it will keep doing that until somebody looks.",
"short_answer": """<p>A NAT Gateway is charged <strong>per hour it exists</strong>, not per byte it moves. At $0.045/hour in us-east-1 that is roughly <strong>$32.40 a month</strong> before any data-processing charge, and it applies to a gateway sitting completely idle.</p>
<p>CloudWatch publishes <code>BytesOutToDestination</code> per gateway. If that is flat zero across a fortnight, nothing is using it. The script below finds those, and &mdash; because deleting a gateway can cut off a workload you have not thought of &mdash; it reports by default and needs an explicit flag to delete.</p>""",
"problem": """<p>Nothing breaks and nothing alerts. The gateway shows as <em>available</em>, which reads like health rather than cost. Cost Explorer files it under <code>EC2-Other</code>, which is one of the least legible lines on an AWS bill, so even somebody looking at spend will not obviously see it.</p>
<p>It compounds. NAT Gateways are per availability zone, so a three-AZ VPC built for redundancy has three of them at roughly <strong>$97 a month</strong> combined. Multiply by a staging VPC nobody deleted and a proof of concept from last year, and this single line is often the largest piece of an unexplained bill.</p>""",
"why": """<p><strong>Hourly billing hides idleness.</strong> Most AWS cost intuition is usage-based: no traffic, no charge. NAT Gateway breaks that intuition, and the break is exactly what makes it easy to leave running.</p>
<p><strong>They outlive their reason.</strong> The usual sequence is a private subnet that needed to reach S3, later replaced by a gateway VPC endpoint &mdash; which is free &mdash; without anyone removing the NAT Gateway that endpoint made redundant.</p>
<p><strong>Deleting one feels risky, so nobody does.</strong> If a Lambda or an ECS task in a private subnet still routes through it, deleting it breaks outbound traffic in a way that surfaces as timeouts rather than a clear error. That risk is real, which is why the check below measures actual traffic before recommending anything.</p>""",
"steps": [
 {"h": "List every gateway and its age",
  "body": """<p>Start with what exists. A gateway in any state other than <code>deleted</code> is billing.</p>
<pre><code class="language-bash">aws ec2 describe-nat-gateways \\
  --filter Name=state,Values=available \\
  --query 'NatGateways[].{Id:NatGatewayId,VPC:VpcId,Subnet:SubnetId,Since:CreateTime}'</code></pre>"""},
 {"h": "Measure traffic, do not guess",
  "body": """<p>CloudWatch has <code>BytesOutToDestination</code> for the <code>AWS/NATGateway</code> namespace. Sum it over at least fourteen days &mdash; a week can miss anything that runs fortnightly, and a monthly batch job is exactly the workload you do not want to cut off.</p>"""},
 {"h": "Check what still routes through it",
  "body": """<p>Before deleting, find the route tables pointing at the gateway. A route table with associated subnets means something may still depend on it, even if it has been quiet.</p>
<pre><code class="language-bash">aws ec2 describe-route-tables \\
  --filters Name=route.nat-gateway-id,Values=nat-0abc123 \\
  --query 'RouteTables[].{Id:RouteTableId,Assoc:Associations[].SubnetId}'</code></pre>"""},
 {"h": "Consider whether you needed it at all",
  "body": """<p>If the only outbound traffic was to S3 or DynamoDB, a <strong>gateway VPC endpoint costs nothing</strong> &mdash; no hourly charge and no per-GB charge. Interface endpoints are $0.01/hour plus $0.01/GB, still far below NAT. Replacing NAT with endpoints is usually the real fix rather than simply deleting.</p>"""},
],
"verify": """<p>Confirm the gateway is gone and nothing started failing:</p>
<pre><code class="language-bash">aws ec2 describe-nat-gateways --nat-gateway-ids nat-0abc123 \\
  --query 'NatGateways[].State'
# "deleted"</code></pre>
<p>Then watch the workloads that shared its VPC for a full cycle of whatever they do &mdash; a nightly job, a weekly report. Timeouts to external hosts are the symptom of having cut off something that mattered.</p>""",
"code_intro": "The script lists every available NAT Gateway, pulls fourteen days of egress from CloudWatch, and reports the ones that moved no bytes along with what each is costing. Deletion requires both <code>--apply</code> and the specific gateway id: it will not bulk-delete, because a quiet gateway and an unused one are not the same thing.",
"py_file": "nat_gateway_idle_audit.py",
"py": '''"""Find NAT Gateways with no traffic and report what they cost.

A NAT Gateway bills per hour it exists, so an idle one is pure waste. But quiet is
not the same as unused -- a monthly batch job looks idle for 29 days -- so this
reports by default and deletes only a gateway you name explicitly.
"""
import argparse
import datetime as dt
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("nat_gateway_idle_audit")

# us-east-1 list price, August 2026. Other regions differ; see the sources.
HOURLY_USD = 0.045
MONTHLY_USD = HOURLY_USD * 24 * 30


def egress_bytes(cw, nat_id, days):
    """Total bytes out to the internet over the window."""
    end = dt.datetime.now(dt.timezone.utc)
    points = cw.get_metric_statistics(
        Namespace="AWS/NATGateway",
        MetricName="BytesOutToDestination",
        Dimensions=[{"Name": "NatGatewayId", "Value": nat_id}],
        StartTime=end - dt.timedelta(days=days),
        EndTime=end,
        Period=86400,
        Statistics=["Sum"],
    )["Datapoints"]
    return sum(p["Sum"] for p in points)


def verdict(total_bytes, days, threshold_bytes=1_000_000):
    """Pure decision function.

    A threshold rather than zero, because health checks and DNS produce a trickle
    on a gateway nothing actually uses. A megabyte over two weeks is noise.
    """
    if total_bytes <= threshold_bytes:
        return "IDLE", f"{total_bytes:,.0f} bytes in {days} days"
    return "IN USE", f"{total_bytes / 1e9:.2f} GB in {days} days"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--delete", help="NAT Gateway id to delete")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ec2 = boto3.client("ec2", region_name=args.region)
    cw = boto3.client("cloudwatch", region_name=args.region)

    gws = ec2.describe_nat_gateways(
        Filter=[{"Name": "state", "Values": ["available"]}])["NatGateways"]
    if not gws:
        log.info("no available NAT Gateways in %s", args.region)
        return 0

    idle_cost = 0.0
    for gw in gws:
        nat_id = gw["NatGatewayId"]
        state, detail = verdict(egress_bytes(cw, nat_id, args.days), args.days)
        line = f"{nat_id} in {gw['VpcId']} -- {detail}, ~${MONTHLY_USD:.2f}/month"
        if state == "IDLE":
            idle_cost += MONTHLY_USD
            log.warning("IDLE   %s", line)
        else:
            log.info("IN USE %s", line)

    if idle_cost:
        log.warning("idle NAT Gateways are costing about $%.2f/month", idle_cost)
        log.warning("check route tables before deleting: "
                    "aws ec2 describe-route-tables --filters "
                    "Name=route.nat-gateway-id,Values=<id>")

    if args.delete:
        if args.apply:
            ec2.delete_nat_gateway(NatGatewayId=args.delete)
            log.info("deleting %s", args.delete)
        else:
            log.info("WOULD delete %s -- pass --apply", args.delete)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "nat-gateway-idle-audit.mjs",
"js": '''/**
 * Find NAT Gateways with no traffic and report what they cost.
 *
 * A NAT Gateway bills per hour it exists, so an idle one is pure waste. But quiet
 * is not the same as unused -- a monthly batch job looks idle for 29 days -- so
 * this reports by default and deletes only a gateway you name explicitly.
 */
import { EC2Client, DescribeNatGatewaysCommand, DeleteNatGatewayCommand } from '@aws-sdk/client-ec2';
import { CloudWatchClient, GetMetricStatisticsCommand } from '@aws-sdk/client-cloudwatch';

// us-east-1 list price, August 2026. Other regions differ; see the sources.
const HOURLY_USD = 0.045;
const MONTHLY_USD = HOURLY_USD * 24 * 30;

async function egressBytes(cw, natId, days) {
  const EndTime = new Date();
  const StartTime = new Date(EndTime.getTime() - days * 86400_000);
  const out = await cw.send(new GetMetricStatisticsCommand({
    Namespace: 'AWS/NATGateway',
    MetricName: 'BytesOutToDestination',
    Dimensions: [{ Name: 'NatGatewayId', Value: natId }],
    StartTime, EndTime, Period: 86400, Statistics: ['Sum'],
  }));
  return (out.Datapoints ?? []).reduce((t, p) => t + (p.Sum ?? 0), 0);
}

/**
 * Pure decision function.
 *
 * A threshold rather than zero, because health checks and DNS produce a trickle on
 * a gateway nothing actually uses. A megabyte over two weeks is noise.
 */
export function verdict(totalBytes, days, thresholdBytes = 1_000_000) {
  if (totalBytes <= thresholdBytes) {
    return { state: 'IDLE', detail: `${totalBytes.toLocaleString()} bytes in ${days} days` };
  }
  return { state: 'IN USE', detail: `${(totalBytes / 1e9).toFixed(2)} GB in ${days} days` };
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const days = Number(process.env.DAYS ?? 14);
  const apply = process.argv.includes('--apply');
  const toDelete = process.argv[process.argv.indexOf('--delete') + 1];

  const ec2 = new EC2Client({ region });
  const cw = new CloudWatchClient({ region });

  const { NatGateways = [] } = await ec2.send(new DescribeNatGatewaysCommand({
    Filter: [{ Name: 'state', Values: ['available'] }],
  }));
  if (!NatGateways.length) return console.log(`no available NAT Gateways in ${region}`);

  let idleCost = 0;
  for (const gw of NatGateways) {
    const { state, detail } = verdict(await egressBytes(cw, gw.NatGatewayId, days), days);
    const line = `${gw.NatGatewayId} in ${gw.VpcId} -- ${detail}, ~$${MONTHLY_USD.toFixed(2)}/month`;
    if (state === 'IDLE') { idleCost += MONTHLY_USD; console.warn(`IDLE   ${line}`); }
    else console.log(`IN USE ${line}`);
  }
  if (idleCost) {
    console.warn(`idle NAT Gateways are costing about $${idleCost.toFixed(2)}/month`);
  }

  if (process.argv.includes('--delete')) {
    if (apply) {
      await ec2.send(new DeleteNatGatewayCommand({ NatGatewayId: toDelete }));
      console.log(`deleting ${toDelete}`);
    } else {
      console.log(`WOULD delete ${toDelete} -- pass --apply`);
    }
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The threshold is the interesting part: exactly zero bytes almost never happens, because health checks and DNS leak a trickle through a gateway nothing really uses. The test pins down where the line sits.",
"test_py_file": "test_nat_gateway_idle_audit.py",
"test_py": '''from nat_gateway_idle_audit import verdict


def test_zero_traffic_is_idle():
    state, _ = verdict(0, 14)
    assert state == "IDLE"


def test_a_trickle_is_still_idle():
    """Health checks and DNS leak bytes through a gateway nothing really uses."""
    state, _ = verdict(500_000, 14)
    assert state == "IDLE"


def test_real_traffic_is_in_use():
    state, detail = verdict(5_000_000_000, 14)
    assert state == "IN USE"
    assert "GB" in detail


def test_the_threshold_boundary_is_inclusive():
    assert verdict(1_000_000, 14)[0] == "IDLE"
    assert verdict(1_000_001, 14)[0] == "IN USE"
''',
"test_js_file": "nat-gateway-idle-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './nat-gateway-idle-audit.mjs';

test('zero traffic is idle', () => {
  assert.equal(verdict(0, 14).state, 'IDLE');
});

test('a trickle is still idle', () => {
  assert.equal(verdict(500_000, 14).state, 'IDLE');
});

test('real traffic is in use', () => {
  const { state, detail } = verdict(5_000_000_000, 14);
  assert.equal(state, 'IN USE');
  assert.match(detail, /GB/);
});

test('the threshold boundary is inclusive', () => {
  assert.equal(verdict(1_000_000, 14).state, 'IDLE');
  assert.equal(verdict(1_000_001, 14).state, 'IN USE');
});
''',
"faq": [
 ("How much does an idle NAT Gateway actually cost?",
  "About $32.40 a month in us-east-1, from the $0.045 per gateway-hour charge alone. Data processing is billed separately at $0.045/GB, so an idle gateway pays the hourly charge and nothing else — which is exactly why it goes unnoticed."),
 ("Why does it cost anything if no traffic passes through it?",
  "Because the charge is for the gateway existing, not for what it carries. Most AWS cost intuition is usage-based, and this breaks that intuition, which is what makes it easy to leave running for months."),
 ("Is it safe to delete a gateway with no traffic?",
  "Not automatically. A workload that runs monthly looks idle for 29 days out of 30. Check the route tables that point at it and whether their subnets have anything in them before deleting, which is why the script needs an explicit id rather than deleting everything it flags."),
 ("What should I use instead?",
  "If the traffic was to S3 or DynamoDB, a gateway VPC endpoint costs nothing at all — no hourly charge, no per-GB charge. Interface endpoints are $0.01/hour plus $0.01/GB, still far cheaper than NAT. Replacing rather than deleting is usually the real fix."),
 ("Why do I have three of them?",
  "NAT Gateways are per availability zone. A three-AZ VPC built for redundancy has three, at roughly $97 a month combined. That is correct for production; it is waste in a staging VPC nobody uses."),
],
"related": [
 ("/aws/public-ipv4-now-always-charged/", "Public IPv4 is charged even when attached"),
 ("/aws/unattached-ebs-volumes/", "Unattached EBS volumes bill exactly like attached ones"),
 ("/build/", "AWS architecture walkthroughs"),
],
"citations": [CITE_NAT, CITE_EC2,
 ("boto3 ec2 describe_nat_gateways",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_nat_gateways.html"),
 ("Gateway endpoints for Amazon S3 — AWS docs",
  "https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html")],
},

{
"slug": "public-ipv4-now-always-charged",
"title": "Public IPv4 Is Charged Even When It Is Attached",
"description": "Most advice says an Elastic IP only costs money when unattached. Since February 2024 every public IPv4 address is charged hourly, attached or not.",
"h1": "public IPv4 is charged even when it is attached",
"category": "AWS cost",
"pill": "Cost",
"chips": ["EC2 API", "Python and Node.js", "Advice that went stale"],
"keywords": ["Elastic IP cost", "public IPv4 charge", "AWS IPv4 pricing 2024",
             "unattached Elastic IP", "Public IP Insights"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-ec2",
"lead": "Search for Elastic IP costs and you will find the same advice everywhere: an address is free while it is attached to a running instance, and only costs money when it is not. That was true, and it stopped being true on <strong>1 February 2024</strong>. Every public IPv4 address now costs $0.005 an hour whether it is attached to anything or not, which is roughly <strong>$3.60 a month each</strong> &mdash; and most of the advice online still has not caught up.",
"short_answer": """<p>Since 1 February 2024, AWS charges <strong>$0.005 per hour for every public IPv4 address</strong>, in use or idle. The old rule &mdash; free when attached, charged when not &mdash; no longer applies.</p>
<p>That is about <strong>$3.60 per address per month</strong>, and it covers addresses you may not think of as yours: internet-facing load balancers, NAT Gateways, RDS instances with public access, EKS nodes. Finding them is an <code>ec2 describe-addresses</code> call plus a sweep of the services that allocate their own.</p>""",
"problem": """<p>The bill grows by an amount that does not obviously map to anything. Each address is small, so no single line looks wrong, and the total sits inside <code>EC2-Other</code> where it is hard to attribute.</p>
<p>The bigger problem is the stale mental model. A team that believes attached addresses are free will not think to count them, so an account with forty instances each holding a public IP carries around <strong>$144 a month</strong> that nobody has ever looked at. Worse, the standard remedy people reach for &mdash; releasing unattached addresses &mdash; only touches a fraction of the total.</p>""",
"why": """<p><strong>The pricing changed and the internet did not.</strong> Years of blog posts, Stack Overflow answers and internal runbooks encode the old rule. AWS made the change because IPv4 addresses are scarce and acquisition costs rose sharply, but that reasoning did not reach the second page of search results.</p>
<p><strong>Many addresses are allocated by other services.</strong> You did not create the public IP on your ALB or your NAT Gateway; the service did. They are still charged, and they do not appear in the Elastic IP list where people look.</p>
<p><strong>The free tier masks it early on.</strong> The EC2 free tier includes 750 hours of public IPv4 per month for the first twelve months, which is one address running continuously. Accounts feel the change only after the first year or the second instance.</p>""",
"steps": [
 {"h": "Count the addresses you allocated",
  "body": """<p>These are the ones people already know about, and they are still worth listing because the association status changes what you can do, not whether you are charged.</p>
<pre><code class="language-bash">aws ec2 describe-addresses \\
  --query 'Addresses[].{IP:PublicIp,Assoc:AssociationId,Instance:InstanceId}'</code></pre>"""},
 {"h": "Count the ones AWS allocated for you",
  "body": """<p>Network interfaces carry public IPs assigned by load balancers, NAT Gateways and managed databases. <code>describe-network-interfaces</code> is where they surface, and it is the step most audits skip.</p>"""},
 {"h": "Release what is genuinely unused",
  "body": """<p>An unassociated Elastic IP is the easy win: nothing depends on it and releasing is one call. Be careful that the address is not simply between instances during a deploy &mdash; the script reports how long it has been idle where it can.</p>"""},
 {"h": "Reduce the count, not just the idle ones",
  "body": """<p>The real saving is architectural. Instances in private subnets behind one load balancer need no public IP each. IPv6 is free of this charge entirely. Consolidating forty public addresses down to two is a far bigger number than releasing the three that happen to be detached today.</p>"""},
],
"verify": """<p>Count before and after. The number that matters is total public IPv4 addresses, not unattached ones:</p>
<pre><code class="language-bash">aws ec2 describe-addresses --query 'length(Addresses)'
aws ec2 describe-network-interfaces \\
  --query 'length(NetworkInterfaces[?Association.PublicIp!=null])'</code></pre>
<p>Multiply the total by $3.60 and compare it against the <code>EC2-Other</code> line next month.</p>""",
"code_intro": "The script counts every public IPv4 address in the region &mdash; both Elastic IPs you allocated and addresses attached to network interfaces by other services &mdash; and totals what they cost. Release requires an explicit allocation id and <code>--apply</code>, because releasing an address in use during a deploy is disruptive and irreversible.",
"py_file": "public_ipv4_audit.py",
"py": '''"""Count every charged public IPv4 address and total the monthly cost.

Since 1 February 2024 AWS charges for ALL public IPv4 addresses, attached or not,
so counting only the unassociated ones -- which is what most published advice
tells you to do -- misses the majority of the bill.
"""
import argparse
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("public_ipv4_audit")

# Charged since 2024-02-01 for every public IPv4 address, in use or idle.
HOURLY_USD = 0.005
MONTHLY_USD = HOURLY_USD * 24 * 30


def summarise(elastic_ips, interface_ips):
    """Pure decision function over two lists of addresses.

    Splits the total into what you can release today and what needs an
    architectural change, because those are different pieces of work.
    """
    releasable = [a for a in elastic_ips if not a.get("AssociationId")]
    attached_eip = [a for a in elastic_ips if a.get("AssociationId")]
    total = len(elastic_ips) + len(interface_ips)
    return {
        "total": total,
        "monthly_usd": total * MONTHLY_USD,
        "releasable_now": releasable,
        "attached_elastic": len(attached_eip),
        "service_allocated": len(interface_ips),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--release", help="allocation id of an unassociated address")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ec2 = boto3.client("ec2", region_name=args.region)

    eips = ec2.describe_addresses()["Addresses"]
    # Addresses other services allocated: ALBs, NAT Gateways, public RDS, EKS nodes.
    enis = [n for n in ec2.describe_network_interfaces()["NetworkInterfaces"]
            if n.get("Association", {}).get("PublicIp")
            and not n.get("Association", {}).get("AllocationId")]

    s = summarise(eips, enis)
    log.info("%d public IPv4 addresses -- about $%.2f/month",
             s["total"], s["monthly_usd"])
    log.info("  %d Elastic IPs attached to something", s["attached_elastic"])
    log.info("  %d allocated by other services (ALB, NAT, RDS, EKS)",
             s["service_allocated"])
    for a in s["releasable_now"]:
        log.warning("  RELEASABLE %s (allocation %s) -- $%.2f/month",
                    a["PublicIp"], a.get("AllocationId"), MONTHLY_USD)

    if not s["releasable_now"]:
        log.info("nothing is unassociated; the saving here is architectural, "
                 "not a cleanup -- fewer public addresses, not fewer idle ones")

    if args.release:
        if args.apply:
            ec2.release_address(AllocationId=args.release)
            log.info("released %s", args.release)
        else:
            log.info("WOULD release %s -- pass --apply", args.release)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "public-ipv4-audit.mjs",
"js": '''/**
 * Count every charged public IPv4 address and total the monthly cost.
 *
 * Since 1 February 2024 AWS charges for ALL public IPv4 addresses, attached or
 * not, so counting only the unassociated ones -- which is what most published
 * advice tells you to do -- misses the majority of the bill.
 */
import {
  EC2Client,
  DescribeAddressesCommand,
  DescribeNetworkInterfacesCommand,
  ReleaseAddressCommand,
} from '@aws-sdk/client-ec2';

// Charged since 2024-02-01 for every public IPv4 address, in use or idle.
const HOURLY_USD = 0.005;
const MONTHLY_USD = HOURLY_USD * 24 * 30;

/**
 * Pure decision function over two lists of addresses.
 *
 * Splits the total into what you can release today and what needs an
 * architectural change, because those are different pieces of work.
 */
export function summarise(elasticIps, interfaceIps) {
  const releasable = elasticIps.filter((a) => !a.AssociationId);
  const total = elasticIps.length + interfaceIps.length;
  return {
    total,
    monthlyUsd: total * MONTHLY_USD,
    releasableNow: releasable,
    attachedElastic: elasticIps.length - releasable.length,
    serviceAllocated: interfaceIps.length,
  };
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const apply = process.argv.includes('--apply');
  const release = process.argv[process.argv.indexOf('--release') + 1];
  const ec2 = new EC2Client({ region });

  const { Addresses = [] } = await ec2.send(new DescribeAddressesCommand({}));
  const { NetworkInterfaces = [] } = await ec2.send(new DescribeNetworkInterfacesCommand({}));
  const enis = NetworkInterfaces.filter(
    (n) => n.Association?.PublicIp && !n.Association?.AllocationId);

  const s = summarise(Addresses, enis);
  console.log(`${s.total} public IPv4 addresses -- about $${s.monthlyUsd.toFixed(2)}/month`);
  console.log(`  ${s.attachedElastic} Elastic IPs attached to something`);
  console.log(`  ${s.serviceAllocated} allocated by other services (ALB, NAT, RDS, EKS)`);
  for (const a of s.releasableNow) {
    console.warn(`  RELEASABLE ${a.PublicIp} (allocation ${a.AllocationId}) -- $${MONTHLY_USD.toFixed(2)}/month`);
  }
  if (!s.releasableNow.length) {
    console.log('nothing is unassociated; the saving here is architectural, not a cleanup');
  }

  if (process.argv.includes('--release')) {
    if (apply) {
      await ec2.send(new ReleaseAddressCommand({ AllocationId: release }));
      console.log(`released ${release}`);
    } else {
      console.log(`WOULD release ${release} -- pass --apply`);
    }
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The whole point of the note is that attached addresses count too, so the test that matters is the one asserting an account with nothing releasable still has a bill.",
"test_py_file": "test_public_ipv4_audit.py",
"test_py": '''from public_ipv4_audit import summarise, MONTHLY_USD


def test_attached_addresses_still_cost_money():
    """The heart of it: nothing is releasable, and there is still a bill."""
    eips = [{"PublicIp": "1.2.3.4", "AssociationId": "eipassoc-1"}]
    s = summarise(eips, [])
    assert s["releasable_now"] == []
    assert s["monthly_usd"] > 0


def test_service_allocated_addresses_are_counted():
    s = summarise([], [{"Association": {"PublicIp": "5.6.7.8"}}] * 3)
    assert s["total"] == 3
    assert s["service_allocated"] == 3


def test_unassociated_addresses_are_flagged():
    eips = [{"PublicIp": "1.2.3.4", "AllocationId": "eipalloc-1"}]
    s = summarise(eips, [])
    assert len(s["releasable_now"]) == 1


def test_total_cost_is_per_address():
    s = summarise([{"PublicIp": "a", "AssociationId": "x"}] * 10, [])
    assert round(s["monthly_usd"], 2) == round(10 * MONTHLY_USD, 2)


def test_empty_account_is_free():
    assert summarise([], [])["monthly_usd"] == 0
''',
"test_js_file": "public-ipv4-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { summarise } from './public-ipv4-audit.mjs';

test('attached addresses still cost money', () => {
  const s = summarise([{ PublicIp: '1.2.3.4', AssociationId: 'eipassoc-1' }], []);
  assert.deepEqual(s.releasableNow, []);
  assert.ok(s.monthlyUsd > 0);
});

test('service-allocated addresses are counted', () => {
  const enis = Array.from({ length: 3 }, () => ({ Association: { PublicIp: '5.6.7.8' } }));
  const s = summarise([], enis);
  assert.equal(s.total, 3);
  assert.equal(s.serviceAllocated, 3);
});

test('unassociated addresses are flagged', () => {
  const s = summarise([{ PublicIp: '1.2.3.4', AllocationId: 'eipalloc-1' }], []);
  assert.equal(s.releasableNow.length, 1);
});

test('an empty account is free', () => {
  assert.equal(summarise([], []).monthlyUsd, 0);
});
''',
"faq": [
 ("Is an attached Elastic IP still free?",
  "No. That changed on 1 February 2024. Every public IPv4 address is charged $0.005 per hour whether it is attached to a running instance or sitting idle. A great deal of published advice still describes the old rule."),
 ("How much is that per address?",
  "About $3.60 a month, or $43.20 a year, per address. Individually trivial, which is why an account with forty of them carries roughly $144 a month that nobody has counted."),
 ("Which addresses count?",
  "All of them, including ones you did not allocate yourself: internet-facing load balancers, NAT Gateways, RDS instances with public access, EKS nodes. They do not appear in the Elastic IP list, which is why audits that only check describe-addresses undercount."),
 ("Does the free tier cover this?",
  "The EC2 free tier includes 750 hours of public IPv4 per month for the first twelve months — one address running continuously. Accounts typically notice the charge after the first year or the second instance."),
 ("What is the actual fix?",
  "Fewer public addresses, not fewer idle ones. Instances in private subnets behind a single load balancer need no public IP each. IPv6 carries no equivalent charge. Releasing the odd detached address is worth doing but it is not where the money is."),
],
"related": [
 ("/aws/nat-gateway-idle-with-no-traffic/", "An idle NAT Gateway still costs $32 a month"),
 ("/aws/unattached-ebs-volumes/", "Unattached EBS volumes bill exactly like attached ones"),
 ("/dns/", "DNS and domain field notes"),
],
"citations": [CITE_IPV4, CITE_EC2,
 ("Elastic IP addresses — Amazon EC2 user guide",
  "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html"),
 ("boto3 ec2 describe_addresses",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_addresses.html")],
},

]
